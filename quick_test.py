#!/usr/bin/env python3
"""
快速测试脚本 - 不需要用户输入
"""

import json
import cv2
import numpy as np
import pytesseract
from mss import mss

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

def load_rois(path: str):
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)

def main():
	print("=== 快速OCR测试 ===")
	
	# 检查rois.json
	try:
		rois = load_rois("rois.json")
		print(f"✓ ROI配置加载成功，包含 {len(rois)} 个板块")
	except Exception as e:
		print(f"✗ ROI配置加载失败: {e}")
		return
	
	# 截图测试
	try:
		with mss() as sct:
			print("正在截图...")
			img = grab_fullscreen(sct)
			print(f"✓ 截图成功，图像尺寸: {img.shape}")
			
			# 测试第一个板块
			# name = PANEL_NAMES[0]
			for name in rois:
				x1, y1, w1, h1 = rois[name]["power"]
				x2, y2, w2, h2 = rois[name]["grade"]
				
				crop_power = img[y1:y1+h1, x1:x1+w1]
				crop_grade = img[y2:y2+h2, x2:x2+w2]
				
				print(f"✓ 裁剪成功: {name}")
				print(f"  主力等级区域: {crop_power.shape}")
				print(f"  级别区域: {crop_grade.shape}")
				
				# 保存测试图像
				cv2.imwrite(f"test_{name}_power.png", crop_power)
				cv2.imwrite(f"test_{name}_grade.png", crop_grade)
				print(f"✓ 测试图像已保存")
				
				# 测试OCR
				try:
					# 简单的OCR测试
					gray_power = cv2.cvtColor(crop_power, cv2.COLOR_BGR2GRAY)
					gray_grade = cv2.cvtColor(crop_grade, cv2.COLOR_BGR2GRAY)
					
					text_power = pytesseract.image_to_string(gray_power, config='--psm 7')
					text_grade = pytesseract.image_to_string(gray_grade, config='--psm 8')
					
					print(f"✓ OCR测试成功:")
					print(f"  主力等级识别: '{text_power.strip()}'")
					print(f"  级别识别: '{text_grade.strip()}'")
					
				except Exception as e:
					print(f"✗ OCR测试失败: {e}")
					print("请检查Tesseract OCR是否正确安装")
			# else:
			# 	print(f"✗ 板块 {name} 不在ROI配置中")
				
	except Exception as e:
		print(f"✗ 截图测试失败: {e}")
	
	print("\n=== 测试完成 ===")
	print("如果看到 ✓，说明基本功能正常")
	print("如果看到 ✗，请检查对应的问题")

if __name__ == "__main__":
	main()
