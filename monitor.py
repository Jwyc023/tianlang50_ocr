# -*- coding: utf-8 -*-
"""
实时监控脚本 - 每秒识别8个板块的主力等级和级别，判断做多/做空信号
作者：AI助手
功能：全屏截图 -> OCR识别 -> 信号判断 -> CSV保存
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple

import cv2
import numpy as np
import pytesseract
from mss import mss

# Tesseract OCR 路径配置（Windows用户需要设置）
# 如果运行时提示找不到tesseract，请取消下行注释并设置正确路径
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# 8个监控板块的名称（必须与rois.json中的键名完全一致）
PANEL_NAMES = [
	"中证1000",    # 第1个板块
	"中证500",     # 第2个板块
	"沪深300",     # 第3个板块
	"上证50",      # 第4个板块
	"上证指数",    # 第5个板块
	"深证成指",    # 第6个板块
	"科创50",      # 第7个板块
	"创业板指",    # 第8个板块
]

# 级别排序：从低到高（C最低，AAA最高）
# 这个顺序用于判断是否达到A级及以上
GRADES_ORDER = ["C", "B", "A", "AA", "AAA"]


def grab_fullscreen(sct: mss) -> np.ndarray:
	"""
	全屏截图函数
	
	设计思路：
	- 使用mss库进行高性能截图（比PIL.ImageGrab快很多）
	- 只取RGB三个通道，去掉Alpha通道（提高处理速度）
	- 返回numpy数组格式，方便后续OpenCV处理
	
	参数：
	- sct: mss截图对象
	
	返回：
	- numpy数组格式的BGR图像（OpenCV标准格式）
	"""
	monitor = sct.monitors[0]  # 获取主显示器
	img = np.array(sct.grab(monitor))  # 截图并转换为numpy数组
	return img[:, :, :3]  # 只保留RGB三个通道，去掉Alpha通道


def preprocess_for_ocr(img: np.ndarray, is_grade: bool = False) -> np.ndarray:
	"""
	图像预处理函数 - 为OCR识别优化图像质量
	
	设计思路：
	- 主力等级（数字）：使用较小的放大倍数，自适应阈值（适合数字识别）
	- 级别（文本）：使用较大的放大倍数，OTSU阈值（适合文本识别）
	- 通过不同的预处理策略提高识别准确率
	
	参数：
	- img: 原始BGR图像
	- is_grade: 是否为级别文本（True=级别，False=主力等级）
	
	返回：
	- 预处理后的二值化图像（黑白图像，适合OCR）
	"""
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 转换为灰度图
	
	if is_grade:
		# 级别文本预处理：更大的放大倍数，适合文本识别
		gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)  # 4倍放大
		blur = cv2.GaussianBlur(gray, (5, 5), 0)  # 高斯去噪（5x5核）
		_, thr = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # OTSU自动阈值
	else:
		# 主力等级数字预处理：较小的放大倍数，适合数字识别
		gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)  # 2倍放大
		blur = cv2.GaussianBlur(gray, (3, 3), 0)  # 高斯去噪（3x3核）
		thr = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8)  # 自适应阈值
	
	return thr


def ocr_text(img: np.ndarray, psm: int = 7) -> str:
	"""
	OCR文本识别函数
	
	设计思路：
	- 使用Tesseract OCR引擎进行文字识别
	- PSM=7：单行文本模式（适合数字和短文本）
	- PSM=8：单词模式（适合单个单词识别）
	- 支持中英文混合识别
	
	参数：
	- img: 预处理后的二值化图像
	- psm: 页面分割模式（7=单行，8=单词）
	
	返回：
	- 识别出的文本字符串
	"""
	cfg = f"--psm {psm} -l eng+chi_sim"  # 配置：PSM模式 + 中英文语言包
	text = pytesseract.image_to_string(img, config=cfg)  # 执行OCR识别
	return text.strip()  # 去除首尾空白字符


def parse_power(text: str) -> float:
	"""
	主力等级数值解析函数
	
	设计思路：
	- OCR识别经常出现字符误识别（如O→0，—→-等）
	- 通过字符替换和过滤，提取纯数字部分
	- 容错处理：如果解析失败返回NaN
	
	参数：
	- text: OCR识别出的原始文本
	
	返回：
	- 解析后的浮点数（失败时返回NaN）
	"""
	# 清理常见OCR错误
	t = text.replace(" ", "").replace("O", "0").replace("o", "0").replace("—", "-")
	t = t.replace("+", "+").replace(",", "").replace("％", "%").replace("%", "")
	
	# 提取数字字符（包括正负号和小数点）
	num = ""
	for ch in t:
		if ch in "+-.0123456789":
			num += ch
	
	# 尝试转换为浮点数
	try:
		return float(num)
	except Exception:
		return float("nan")  # 解析失败返回NaN


def normalize_grade(text: str) -> str:
	"""
	级别文本规范化函数
	
	设计思路：
	- OCR识别级别文本时经常出现误识别
	- 使用宽松的匹配规则（包含匹配而非精确匹配）
	- 支持负号前缀（-A, -AA, -AAA等）
	- 容错处理：无法识别时返回空字符串
	
	参数：
	- text: OCR识别出的原始文本
	
	返回：
	- 规范化后的级别字符串（如"A", "AA", "-B"等）
	"""
	# 清理文本，处理常见OCR错误
	t = text.upper().replace(" ", "").replace("- ", "-").replace("—", "-")
	t = t.replace("O", "0").replace("o", "0")  # 处理数字0的误识别
	
	# 提取负号前缀
	sign = ""
	if t.startswith("-"):
		sign = "-"
		t = t[1:]
	
	# 宽松的级别匹配规则（按优先级从高到低）
	grade = ""
	if "AAA" in t or t.startswith("3A"):  # 最高级别
		grade = "AAA"
	elif "AA" in t or t.startswith("2A"):  # 次高级别
		grade = "AA"
	elif t.startswith("A") or "A" in t:    # A级别
		grade = "A"
	elif t.startswith("B") or "B" in t:    # B级别
		grade = "B"
	elif t.startswith("C") or "C" in t:    # C级别
		grade = "C"
	else:
		return ""  # 无法识别时返回空字符串
	
	return sign + grade  # 返回带符号的级别


def grade_rank(grade: str) -> int:
	"""
	级别排序函数
	
	设计思路：
	- 将级别字符串转换为数字排序值
	- 负号不影响排序（-AAA依然高于-C）
	- 用于判断是否达到A级及以上
	
	参数：
	- grade: 级别字符串（如"A", "AA", "-B"等）
	
	返回：
	- 排序值（0=C, 1=B, 2=A, 3=AA, 4=AAA，-1=无效）
	"""
	if not grade:
		return -1  # 空字符串返回-1
	
	# 去掉负号前缀，只保留级别部分
	g = grade[1:] if grade.startswith("-") else grade
	
	try:
		return GRADES_ORDER.index(g)  # 返回在排序列表中的索引
	except ValueError:
		return -1  # 无效级别返回-1


def decide_signal(powers: List[float], grades: List[str]) -> str:
	"""
	信号判断函数 - 核心量化逻辑
	
	设计思路：
	- 做多条件：≥7个正数主力等级 且 ≥3个A级及以上级别
	- 做空条件：≥7个负数主力等级 且 ≥3个-A级及以上级别
	- 其他情况：观望
	
	参数：
	- powers: 8个板块的主力等级列表
	- grades: 8个板块的级别列表
	
	返回：
	- 信号字符串："做多" / "做空" / "观望"
	"""
	# 统计正数和负数的主力等级数量
	pos_cnt = sum(1 for v in powers if isinstance(v, float) and not np.isnan(v) and v > 0)
	neg_cnt = sum(1 for v in powers if isinstance(v, float) and not np.isnan(v) and v < 0)

	# 统计A级及以上的正级别和负级别数量
	high_pos = sum(1 for g in grades if g and not g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))
	high_neg = sum(1 for g in grades if g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))

	# 信号判断逻辑
	if pos_cnt >= 7 and high_pos >= 3:
		return "做多"  # 满足做多条件
	if neg_cnt >= 7 and high_neg >= 3:
		return "做空"  # 满足做空条件
	return "观望"  # 其他情况观望


def load_rois(path: str) -> Dict[str, Dict[str, Tuple[int, int, int, int]]]:
	"""
	加载ROI配置文件
	
	设计思路：
	- 从JSON文件加载每个板块的ROI坐标
	- ROI包含两个区域：power（主力等级）和grade（级别）
	- 每个区域用4个数字表示：(x, y, width, height)
	
	参数：
	- path: ROI配置文件路径
	
	返回：
	- ROI配置字典
	"""
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def main():
	"""
	主函数 - 实时监控循环
	
	设计思路：
	1. 初始化：加载ROI配置，创建CSV文件，设置调试目录
	2. 循环监控：每秒执行一次完整的识别流程
	3. 性能优化：使用精确的时间控制确保1秒间隔
	4. 数据保存：实时写入CSV文件，便于后续分析
	
	流程：
	截图 -> 裁剪ROI -> 图像预处理 -> OCR识别 -> 数据解析 -> 信号判断 -> CSV保存
	"""
	# === 初始化阶段 ===
	print("=== 实时监控系统启动 ===")
	
	# 加载ROI配置
	rois = load_rois("rois.json")
	print(f"✓ ROI配置加载成功，监控 {len(rois)} 个板块")
	
	# 创建输出文件
	out_csv = f"ticks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
	
	# 创建调试目录（用于保存OCR调试图像）
	debug_dir = "debug_images"
	if not os.path.exists(debug_dir):
		os.makedirs(debug_dir)
		print(f"✓ 创建调试目录: {debug_dir}")

	# 设置CSV表头
	header = ["timestamp"]  # 时间戳列
	for name in PANEL_NAMES:
		header += [f"{name}_主力等级", f"{name}_级别"]  # 每个板块两列
	header += ["结论"]  # 信号结论列

	print(f"✓ 输出文件: {out_csv}")
	print("✓ 按 Ctrl+C 停止监控")
	print("✓ 调试图像将保存到 debug_images/ 目录")
	print("\n=== 开始监控循环 ===")

	# === 监控循环阶段 ===
	with open(out_csv, "w", newline="", encoding="utf-8-sig") as fcsv:
		writer = csv.writer(fcsv)
		writer.writerow(header)  # 写入表头
		fcsv.flush()  # 立即刷新到文件

		with mss() as sct:  # 创建高性能截图对象
			cycle_count = 0  # 循环计数器
			start_time = time.time()  # 记录开始时间
			
			while True:
				cycle_start = time.time()  # 记录当前循环开始时间
				cycle_count += 1
				# === 步骤1：全屏截图 ===
				img = grab_fullscreen(sct)
				
				# === 步骤2：初始化数据容器 ===
				powers: List[float] = []  # 存储8个板块的主力等级
				grades: List[str] = []    # 存储8个板块的级别

				# === 步骤3：循环处理每个板块 ===
				for name in PANEL_NAMES:
					# 获取当前板块的ROI坐标
					x1, y1, w1, h1 = rois[name]["power"]   # 主力等级区域
					x2, y2, w2, h2 = rois[name]["grade"]   # 级别区域

					# 从全屏图像中裁剪出两个小区域
					crop_power = img[y1:y1+h1, x1:x1+w1]  # 主力等级区域
					crop_grade = img[y2:y2+h2, x2:x2+w2]  # 级别区域

					# === 步骤4：主力等级识别（数字） ===
					pp = preprocess_for_ocr(crop_power, is_grade=False)  # 数字预处理
					txt_power = ocr_text(pp, psm=7)  # OCR识别（单行模式）
					val_power = parse_power(txt_power)  # 解析为浮点数

					# === 步骤5：级别识别（文本） ===
					pg = preprocess_for_ocr(crop_grade, is_grade=True)  # 文本预处理
					txt_grade = ocr_text(pg, psm=8)  # OCR识别（单词模式）
					val_grade = normalize_grade(txt_grade)  # 规范化级别

					# === 步骤6：保存调试图像（可选） ===
					# 每10秒保存一次调试图像，避免文件过多
					timestamp = datetime.now().strftime("%H%M%S")
					if int(timestamp) % 10 == 0:
						cv2.imwrite(f"{debug_dir}/{name}_power_raw_{timestamp}.png", crop_power)
						cv2.imwrite(f"{debug_dir}/{name}_power_proc_{timestamp}.png", pp)
						cv2.imwrite(f"{debug_dir}/{name}_grade_raw_{timestamp}.png", crop_grade)
						cv2.imwrite(f"{debug_dir}/{name}_grade_proc_{timestamp}.png", pg)

					# 将识别结果添加到列表中
					powers.append(val_power)
					grades.append(val_grade)

				# === 步骤7：信号判断 ===
				signal = decide_signal(powers, grades)
				
				# === 步骤8：准备CSV数据行 ===
				row: List[str] = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]  # 时间戳
				for i in range(8):  # 添加8个板块的数据
					row.append(powers[i])  # 主力等级
					row.append(grades[i])  # 级别
				row.append(signal)  # 信号结论
				
				# === 步骤9：写入CSV文件 ===
				writer.writerow(row)
				fcsv.flush()  # 立即刷新到文件，确保数据不丢失
				
				# === 步骤10：性能优化 - 精确时间控制 ===
				# 计算当前循环耗时
				cycle_elapsed = time.time() - cycle_start
				
				# 显示进度信息（每10次循环显示一次）
				if cycle_count % 10 == 0:
					print(f"第 {cycle_count} 次循环完成，耗时: {cycle_elapsed:.2f}秒，信号: {signal}")
				
				# 确保每秒一次：如果处理时间不足1秒，则等待剩余时间
				sleep_time = max(0, 1.0 - cycle_elapsed)
				if sleep_time > 0:
					time.sleep(sleep_time)
				else:
					# 如果处理时间超过1秒，给出警告
					if cycle_count % 10 == 0:
						print(f"⚠️  警告：处理时间过长 ({cycle_elapsed:.2f}秒)，可能影响实时性")


if __name__ == "__main__":
	main()

