# -*- coding: utf-8 -*-
"""
高性能监控脚本 - 优化版本
主要优化：
1. 减少图像预处理步骤
2. 使用更快的OCR配置
3. 并行处理多个板块
4. 缓存OCR引擎
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

import cv2
import numpy as np
import pytesseract
from mss import mss

# Tesseract OCR 路径配置
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

PANEL_NAMES = [
	"中证1000", "中证500", "沪深300", "上证50",
	"上证指数", "深证成指", "科创50", "创业板指",
]

GRADES_ORDER = ["C", "B", "A", "AA", "AAA"]

# 全局锁，用于线程安全
lock = threading.Lock()

def grab_fullscreen(sct: mss) -> np.ndarray:
	"""快速全屏截图"""
	monitor = sct.monitors[0]
	img = np.array(sct.grab(monitor))
	return img[:, :, :3]

def fast_preprocess(img: np.ndarray, is_grade: bool = False) -> np.ndarray:
	"""快速图像预处理"""
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	if is_grade:
		# 级别：适度放大 + 自适应阈值（更适合单字符）
		gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
		thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
	else:
		# 主力等级：简单放大 + 自适应阈值
		gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
		thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
	
	return thr

def fast_ocr(img: np.ndarray, psm: int = 7, is_grade: bool = False) -> str:
	"""快速OCR识别"""
	# ROI包含中文标签，需要中英文支持
	cfg = f"--psm {psm} -l eng+chi_sim --oem 3"
	text = pytesseract.image_to_string(img, config=cfg)
	return text.strip()

def parse_power(text: str) -> float:
	"""解析主力等级（从包含'主力等级：'的文本中提取数字）"""
	# 移除中文标签和空格
	t = text.replace("主力等级：", "").replace("主力等级", "").replace(" ", "")
	t = t.replace("O", "0").replace("o", "0").replace("—", "-")
	t = t.replace("+", "+").replace(",", "").replace("％", "%").replace("%", "")
	
	# 提取数字部分
	num = ""
	for ch in t:
		if ch in "+-.0123456789":
			num += ch
	
	try:
		return float(num) if num else float("nan")
	except Exception:
		return float("nan")

def normalize_grade(text: str) -> str:
	"""规范化级别（从包含'级别：'的文本中提取级别）"""
	# 移除中文标签
	t = text.replace("级别：", "").replace("级别", "")
	
	# 处理各种分隔符和空格
	t = t.replace(":", "").replace("：", "").replace(" ", "").replace("\t", "")
	t = t.upper().replace("- ", "-").replace("—", "-")
	t = t.replace("O", "0").replace("o", "0")
	
	# 处理更多负号变体
	t = t.replace("一", "-").replace("_", "-").replace("—", "-")
	
	# 调试输出
	print(f"DEBUG normalize_grade: 原始='{text}' -> 处理后='{t}'")
	
	sign = ""
	# 检查各种负号位置
	if t.startswith("-") or t.startswith("一") or t.startswith("_") or t.startswith("—"):
		sign = "-"
		t = t[1:]
	elif "-" in t or "一" in t or "_" in t or "—" in t:
		# 负号在中间，提取负号后的部分
		for sep in ["-", "一", "_", "—"]:
			if sep in t:
				parts = t.split(sep, 1)
				if len(parts) == 2:
					sign = "-"
					t = parts[1]  # 取负号后的部分
				break
	
	grade = ""
	if "AAA" in t or t.startswith("3A"):
		grade = "AAA"
	elif "AA" in t or t.startswith("2A"):
		grade = "AA"
	elif t.startswith("A") or "A" in t:
		grade = "A"
	elif t.startswith("B") or "B" in t:
		grade = "B"
	elif t.startswith("C") or "C" in t:
		grade = "C"
	else:
		print(f"DEBUG normalize_grade: 无法识别级别，剩余文本='{t}'")
		return ""
	
	result = sign + grade
	print(f"DEBUG normalize_grade: 最终结果='{result}'")
	return result

def grade_rank(grade: str) -> int:
	"""级别排序"""
	if not grade:
		return -1
	g = grade[1:] if grade.startswith("-") else grade
	try:
		return GRADES_ORDER.index(g)
	except ValueError:
		return -1

def decide_signal(powers: List[float], grades: List[str]) -> str:
	"""信号判断"""
	pos_cnt = sum(1 for v in powers if isinstance(v, float) and not np.isnan(v) and v > 0)
	neg_cnt = sum(1 for v in powers if isinstance(v, float) and not np.isnan(v) and v < 0)

	high_pos = sum(1 for g in grades if g and not g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))
	high_neg = sum(1 for g in grades if g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))

	if pos_cnt >= 7 and high_pos >= 3:
		return "做多"
	if neg_cnt >= 7 and high_neg >= 3:
		return "做空"
	return "观望"

def process_panel(img: np.ndarray, name: str, rois: Dict) -> Tuple[float, str]:
	"""处理单个板块（用于并行处理）"""
	try:
		x1, y1, w1, h1 = rois[name]["power"]
		x2, y2, w2, h2 = rois[name]["grade"]

		crop_power = img[y1:y1+h1, x1:x1+w1]
		crop_grade = img[y2:y2+h2, x2:x2+w2]

		# 快速预处理
		pp = fast_preprocess(crop_power, is_grade=False)
		pg = fast_preprocess(crop_grade, is_grade=True)

		# 快速OCR
		txt_power = fast_ocr(pp, psm=7, is_grade=False)
		txt_grade = fast_ocr(pg, psm=8, is_grade=True)  # 使用单词模式（优化后）

		# 解析结果
		val_power = parse_power(txt_power)
		val_grade = normalize_grade(txt_grade)
		
		print(f"DEBUG {name}: OCR文本='{txt_grade}', 解析结果='{val_grade}'")

		return val_power, val_grade
	except Exception as e:
		print(f"处理板块 {name} 时出错: {e}")
		import traceback
		traceback.print_exc()
		return float("nan"), ""

def load_rois(path: str) -> Dict[str, Dict[str, Tuple[int, int, int, int]]]:
	"""加载ROI配置"""
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)

def main():
	"""主函数 - 高性能版本"""
	print("=== 高性能监控系统启动 ===")
	
	# 初始化
	rois = load_rois("../data/rois.json")
	out_csv = f"../data/ticks_fast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
	
	# 创建截图保存目录
	screenshot_dir = "../data/fast_screenshots"
	if not os.path.exists(screenshot_dir):
		os.makedirs(screenshot_dir)
		print(f"✓ 创建截图目录: {screenshot_dir}")
	
	header = ["timestamp"]
	for name in PANEL_NAMES:
		header += [f"{name}_主力等级", f"{name}_级别"]
	header += ["结论", "截图文件"]

	print(f"✓ 监控 {len(rois)} 个板块")
	print(f"✓ 输出文件: {out_csv}")
	print(f"✓ 截图目录: {screenshot_dir}")
	print("✓ 使用高性能模式（并行处理 + 截图保存）")
	print("\n=== 开始监控循环 ===")

	with open(out_csv, "w", newline="", encoding="utf-8-sig") as fcsv:
		writer = csv.writer(fcsv)
		writer.writerow(header)
		fcsv.flush()

		with mss() as sct:
			cycle_count = 0
			
			while True:
				cycle_start = time.time()
				cycle_count += 1
				
				# 截图
				img = grab_fullscreen(sct)
				
				# 保存完整页面截图（带时间戳）
				timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
				screenshot_filename = f"{screenshot_dir}/fullscreen_{timestamp}.png"
				cv2.imwrite(screenshot_filename, img)
				
				# 记录当前时间戳（用于CSV）
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				
				# 并行处理所有板块
				with ThreadPoolExecutor(max_workers=4) as executor:
					futures = {}
					for name in PANEL_NAMES:
						future = executor.submit(process_panel, img, name, rois)
						futures[name] = future
					
					# 收集结果（按顺序）
					powers = []
					grades = []
					for name in PANEL_NAMES:
						power, grade = futures[name].result()
						powers.append(power)
						grades.append(grade)
						print(f"DEBUG {name}: 主力等级={power}, 级别='{grade}'")
				
				# 信号判断
				signal = decide_signal(powers, grades)
				
				# 写入CSV（包含截图文件名）
				row = [current_time]
				for i in range(8):
					row.append(powers[i])
					row.append(grades[i])
					print(f"DEBUG CSV写入: {PANEL_NAMES[i]} 主力等级={powers[i]}, 级别='{grades[i]}'")
				row.append(signal)
				row.append(screenshot_filename)  # 添加截图文件名
				
				with lock:
					writer.writerow(row)
					fcsv.flush()
				
				# 时间控制
				cycle_elapsed = time.time() - cycle_start
				
				if cycle_count % 10 == 0:
					print(f"第 {cycle_count} 次循环完成，耗时: {cycle_elapsed:.2f}秒，信号: {signal}")
				
				sleep_time = max(0, 1.0 - cycle_elapsed)
				if sleep_time > 0:
					time.sleep(sleep_time)
				else:
					if cycle_count % 10 == 0:
						print(f"⚠️  警告：处理时间过长 ({cycle_elapsed:.2f}秒)")

if __name__ == "__main__":
	main()
