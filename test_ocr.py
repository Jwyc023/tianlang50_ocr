#!/usr/bin/env python3
"""
OCR测试脚本 - 用于验证ROI区域和OCR识别效果
"""

import json
import cv2
import numpy as np
import pytesseract
from mss import mss

# 如需自定义 tesseract 路径（Windows 常见）请取消下行注释并设置安装路径
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

PANEL_NAMES = [
	"中证1000",
	"中证500", 
	"沪深300",
	"上证50",
	"上证指数",
	"深证成指",
	"科创50",
	"创业板指",
]

def grab_fullscreen(sct: mss) -> np.ndarray:
	monitor = sct.monitors[0]
	img = np.array(sct.grab(monitor))
	return img[:, :, :3]

def preprocess_for_ocr(img: np.ndarray, is_grade: bool = False) -> np.ndarray:
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	# 对于级别文本，使用更大的放大倍数和不同的预处理
	if is_grade:
		gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
		# 更强的去噪
		blur = cv2.GaussianBlur(gray, (5, 5), 0)
		# 使用OTSU阈值
		_, thr = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	else:
		gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
		blur = cv2.GaussianBlur(gray, (3, 3), 0)
		thr = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8)
	
	return thr

def ocr_text(img: np.ndarray, psm: int = 7) -> str:
	cfg = f"--psm {psm} -l eng+chi_sim"
	text = pytesseract.image_to_string(img, config=cfg)
	return text.strip()

def parse_power(text: str) -> float:
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
	# 清理文本，处理常见OCR错误
	t = text.upper().replace(" ", "").replace("- ", "-").replace("—", "-")
	t = t.replace("O", "0").replace("o", "0")  # 处理数字0的误识别
	
	# 提取符号
	sign = ""
	if t.startswith("-"):
		sign = "-"
		t = t[1:]
	
	# 更宽松的匹配规则
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
		# 如果完全无法识别，返回空字符串
		return ""
	
	return sign + grade

def load_rois(path: str):
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)

def main():
	print("OCR测试脚本")
	print("请确保监控页面在前台，然后按回车开始测试...")
	input()
	
	try:
		rois = load_rois("rois.json")
		print(f"成功加载ROI配置，包含 {len(rois)} 个板块")
	except FileNotFoundError:
		print("错误：找不到 rois.json 文件！")
		print("请先运行 python calibrate_rois.py 生成ROI配置")
		return
	except Exception as e:
		print(f"加载ROI配置时出错：{e}")
		return
	
	with mss() as sct:
		print("正在截图...")
		img = grab_fullscreen(sct)
		print(f"截图完成，图像尺寸: {img.shape}")
		
		for name in PANEL_NAMES:
			print(f"\n=== {name} ===")
			
			if name not in rois:
				print(f"警告：{name} 不在ROI配置中，跳过")
				continue
				
			x1, y1, w1, h1 = rois[name]["power"]
			x2, y2, w2, h2 = rois[name]["grade"]
			
			print(f"主力等级ROI: ({x1}, {y1}, {w1}, {h1})")
			print(f"级别ROI: ({x2}, {y2}, {w2}, {h2})")
			
			crop_power = img[y1:y1+h1, x1:x1+w1]
			crop_grade = img[y2:y2+h2, x2:x2+w2]
			
			print(f"主力等级裁剪图像尺寸: {crop_power.shape}")
			print(f"级别裁剪图像尺寸: {crop_grade.shape}")
			
			# 保存原始图像
			cv2.imwrite(f"{name}_power_raw.png", crop_power)
			cv2.imwrite(f"{name}_grade_raw.png", crop_grade)
			print(f"已保存 {name} 的原始图像")
			
			# 主力等级识别
			print("正在处理主力等级...")
			pp = preprocess_for_ocr(crop_power, is_grade=False)
			cv2.imwrite(f"{name}_power_proc.png", pp)
			txt_power = ocr_text(pp, psm=7)
			val_power = parse_power(txt_power)
			print(f"主力等级: '{txt_power}' -> {val_power}")
			
			# 级别识别
			print("正在处理级别...")
			pg = preprocess_for_ocr(crop_grade, is_grade=True)
			cv2.imwrite(f"{name}_grade_proc.png", pg)
			txt_grade = ocr_text(pg, psm=8)
			val_grade = normalize_grade(txt_grade)
			print(f"级别: '{txt_grade}' -> {val_grade}")
			
			# 显示图像
			cv2.imshow(f"{name}_power", crop_power)
			cv2.imshow(f"{name}_grade", crop_grade)
			cv2.waitKey(1000)
	
	cv2.destroyAllWindows()
	print("\n测试完成！请检查生成的图像文件。")

if __name__ == "__main__":
	main()
