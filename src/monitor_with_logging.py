# -*- coding: utf-8 -*-
"""
带详细日志的监控脚本 - 用于诊断null数据问题
功能：
1. 详细日志记录每次识别过程
2. 自动保存识别失败时的截图
3. 记录OCR原始文本和解析结果
4. 提供问题诊断信息
"""

import csv
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple

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

def setup_logging():
	"""设置日志系统"""
	# 创建日志目录
	log_dir = "../data/logs"
	if not os.path.exists(log_dir):
		os.makedirs(log_dir)
	
	# 创建截图目录
	screenshot_dir = "../data/failed_screenshots"
	if not os.path.exists(screenshot_dir):
		os.makedirs(screenshot_dir)
	
	# 设置日志格式
	log_format = '%(asctime)s - %(levelname)s - %(message)s'
	logging.basicConfig(
		level=logging.INFO,
		format=log_format,
		handlers=[
			logging.FileHandler(f'{log_dir}/monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
			logging.StreamHandler()
		]
	)
	
	return log_dir, screenshot_dir

def grab_fullscreen(sct: mss) -> np.ndarray:
	"""全屏截图"""
	monitor = sct.monitors[0]
	img = np.array(sct.grab(monitor))
	return img[:, :, :3]

def preprocess_for_ocr(img: np.ndarray, is_grade: bool = False) -> np.ndarray:
	"""图像预处理"""
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	if is_grade:
		gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
		blur = cv2.GaussianBlur(gray, (5, 5), 0)
		_, thr = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	else:
		gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
		blur = cv2.GaussianBlur(gray, (3, 3), 0)
		thr = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8)
	
	return thr

def ocr_text(img: np.ndarray, psm: int = 7) -> str:
	"""OCR文本识别"""
	cfg = f"--psm {psm} -l eng+chi_sim"
	text = pytesseract.image_to_string(img, config=cfg)
	return text.strip()

def parse_power(text: str) -> float:
	"""解析主力等级"""
	t = text.replace(" ", "").replace("O", "0").replace("o", "0").replace("—", "-")
	t = t.replace("+", "+").replace(",", "").replace("％", "%").replace("%", "")
	num = ""
	for ch in t:
		if ch in "+-.0123456789":
			num += ch
	try:
		return float(num)
	except Exception:
		return float("nan")

def normalize_grade(text: str) -> str:
	"""规范化级别"""
	t = text.upper().replace(" ", "").replace("- ", "-").replace("—", "-")
	t = t.replace("O", "0").replace("o", "0")
	
	sign = ""
	if t.startswith("-"):
		sign = "-"
		t = t[1:]
	
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
		return ""
	
	return sign + grade

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

def load_rois(path: str) -> Dict[str, Dict[str, Tuple[int, int, int, int]]]:
	"""加载ROI配置"""
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)

def save_failed_screenshot(img: np.ndarray, panel_name: str, field_type: str, 
                          roi_coords: Tuple[int, int, int, int], 
                          screenshot_dir: str, timestamp: str):
	"""保存识别失败时的截图"""
	x, y, w, h = roi_coords
	
	# 将中文板块名转换为英文编号，避免文件名乱码
	panel_mapping = {
		"中证1000": "panel01",
		"中证500": "panel02", 
		"沪深300": "panel03",
		"上证50": "panel04",
		"上证指数": "panel05",
		"深证成指": "panel06",
		"科创50": "panel07",
		"创业板指": "panel08"
	}
	panel_id = panel_mapping.get(panel_name, "unknown")
	
	# 保存原始ROI区域
	crop_img = img[y:y+h, x:x+w]
	cv2.imwrite(f"{screenshot_dir}/{panel_id}_{field_type}_raw_{timestamp}.png", crop_img)
	
	# 保存预处理后的图像
	processed_img = preprocess_for_ocr(crop_img, is_grade=(field_type == "grade"))
	cv2.imwrite(f"{screenshot_dir}/{panel_id}_{field_type}_processed_{timestamp}.png", processed_img)
	
	# 保存带ROI标记的全屏截图
	img_marked = img.copy()
	cv2.rectangle(img_marked, (x, y), (x+w, y+h), (0, 0, 255), 3)  # 红色框标记
	cv2.putText(img_marked, f"{panel_id}_{field_type}", (x, y-10), 
	            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
	cv2.imwrite(f"{screenshot_dir}/{panel_id}_{field_type}_marked_{timestamp}.png", img_marked)

def process_panel_with_logging(img: np.ndarray, panel_name: str, rois: Dict, 
                              screenshot_dir: str, timestamp: str) -> Tuple[float, str]:
	"""处理单个板块并记录详细日志"""
	logging.info(f"开始处理板块: {panel_name}")
	
	if panel_name not in rois:
		logging.error(f"板块 {panel_name} 不在ROI配置中")
		return float("nan"), ""
	
	x1, y1, w1, h1 = rois[panel_name]["power"]
	x2, y2, w2, h2 = rois[panel_name]["grade"]
	
	logging.info(f"ROI坐标 - 主力等级: ({x1}, {y1}, {w1}, {h1}), 级别: ({x2}, {y2}, {w2}, {h2})")
	
	# 检查ROI区域是否有效
	if w1 <= 0 or h1 <= 0 or w2 <= 0 or h2 <= 0:
		logging.error(f"无效的ROI坐标: 主力等级({w1}x{h1}), 级别({w2}x{h2})")
		return float("nan"), ""
	
	# 处理主力等级
	crop_power = img[y1:y1+h1, x1:x1+w1]
	logging.info(f"主力等级区域尺寸: {crop_power.shape}")
	
	pp = preprocess_for_ocr(crop_power, is_grade=False)
	txt_power = ocr_text(pp, psm=7)
	val_power = parse_power(txt_power)
	
	logging.info(f"主力等级识别: 原始文本='{txt_power}', 解析结果={val_power}")
	
	# 如果识别失败，保存截图
	if np.isnan(val_power) or val_power == 0:
		logging.warning(f"主力等级识别失败，保存截图")
		save_failed_screenshot(img, panel_name, "power", (x1, y1, w1, h1), screenshot_dir, timestamp)
	
	# 处理级别
	crop_grade = img[y2:y2+h2, x2:x2+w2]
	logging.info(f"级别区域尺寸: {crop_grade.shape}")
	
	pg = preprocess_for_ocr(crop_grade, is_grade=True)
	txt_grade = ocr_text(pg, psm=8)
	val_grade = normalize_grade(txt_grade)
	
	logging.info(f"级别识别: 原始文本='{txt_grade}', 解析结果='{val_grade}'")
	
	# 如果识别失败，保存截图
	if not val_grade:
		logging.warning(f"级别识别失败，保存截图")
		save_failed_screenshot(img, panel_name, "grade", (x2, y2, w2, h2), screenshot_dir, timestamp)
	
	logging.info(f"板块 {panel_name} 处理完成: 主力等级={val_power}, 级别='{val_grade}'")
	return val_power, val_grade

def main():
	"""主函数 - 带详细日志的监控"""
	print("=== 带日志的监控系统启动 ===")
	
	# 确保data目录存在
	if not os.path.exists("../data"):
		os.makedirs("../data")
		print("✓ 创建data目录")
	
	# 设置日志系统
	log_dir, screenshot_dir = setup_logging()
	logging.info("日志系统初始化完成")
	
	# 加载ROI配置
	try:
		rois = load_rois("../data/rois.json")
		logging.info(f"ROI配置加载成功，监控 {len(rois)} 个板块")
	except FileNotFoundError:
		print("❌ 错误：找不到 ../data/rois.json 文件！")
		print("请先运行 python tools/calibrate_rois.py 生成ROI配置")
		return
	except Exception as e:
		print(f"❌ 错误：加载ROI配置失败: {e}")
		return
	
	# 创建输出文件
	out_csv = f"../data/ticks_logged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
	logging.info(f"输出文件: {out_csv}")
	
	# 设置CSV表头
	header = ["timestamp"]
	for name in PANEL_NAMES:
		header += [f"{name}_主力等级", f"{name}_级别"]
	header += ["结论", "日志文件", "截图目录"]
	
	print(f"✓ 日志文件: {log_dir}/")
	print(f"✓ 截图目录: {screenshot_dir}/")
	print(f"✓ 输出文件: {out_csv}")
	print("✓ 按 Ctrl+C 停止监控")
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
				timestamp = datetime.now().strftime("%H%M%S")
				
				logging.info(f"开始第 {cycle_count} 次循环")
				
				# 截图
				img = grab_fullscreen(sct)
				logging.info(f"截图完成，图像尺寸: {img.shape}")
				
				# 处理所有板块
				powers = []
				grades = []
				
				for name in PANEL_NAMES:
					power, grade = process_panel_with_logging(img, name, rois, screenshot_dir, timestamp)
					powers.append(power)
					grades.append(grade)
				
				# 信号判断
				signal = decide_signal(powers, grades)
				logging.info(f"信号判断结果: {signal}")
				
				# 写入CSV
				row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
				for i in range(8):
					row.append(powers[i])
					row.append(grades[i])
				row.append(signal)
				row.append(log_dir)  # 日志文件路径
				row.append(screenshot_dir)  # 截图目录路径
				
				writer.writerow(row)
				fcsv.flush()
				
				# 时间控制
				cycle_elapsed = time.time() - cycle_start
				
				if cycle_count % 10 == 0:
					logging.info(f"第 {cycle_count} 次循环完成，耗时: {cycle_elapsed:.2f}秒，信号: {signal}")
					print(f"第 {cycle_count} 次循环完成，耗时: {cycle_elapsed:.2f}秒，信号: {signal}")
				
				sleep_time = max(0, 1.0 - cycle_elapsed)
				if sleep_time > 0:
					time.sleep(sleep_time)
				else:
					if cycle_count % 10 == 0:
						logging.warning(f"处理时间过长: {cycle_elapsed:.2f}秒")
						print(f"⚠️ 警告：处理时间过长 ({cycle_elapsed:.2f}秒)")

if __name__ == "__main__":
	main()

