#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI预览查看工具
基于现有ROI配置生成带框框的预览图
"""

import json
import os
from datetime import datetime
from typing import Dict, Tuple

import cv2
import numpy as np
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
	"""快速全屏截图"""
	monitor = sct.monitors[0]
	img = np.array(sct.grab(monitor))
	return img[:, :, :3]

def create_roi_preview(img: np.ndarray, rois: Dict[str, Dict[str, list]]) -> np.ndarray:
	"""创建ROI预览图，用不同颜色的框框标出每个区域"""
	preview = img.copy()
	
	# 定义颜色 (BGR格式)
	colors = [
		(0, 255, 0),    # 绿色
		(0, 0, 255),    # 红色
		(255, 0, 0),    # 蓝色
		(0, 255, 255),  # 黄色
		(255, 0, 255),  # 洋红
		(255, 255, 0),  # 青色
		(128, 0, 128),  # 紫色
		(255, 165, 0),  # 橙色
	]
	
	# 为每个板块绘制框框
	for i, (panel_name, panel_rois) in enumerate(rois.items()):
		color = colors[i % len(colors)]
		
		# 绘制主力等级区域
		if "power" in panel_rois:
			power_roi = panel_rois["power"]
			x1, y1, w1, h1 = power_roi
			cv2.rectangle(preview, (x1, y1), (x1 + w1, y1 + h1), color, 2)
			cv2.putText(preview, f"{panel_name}_主力", (x1, y1 - 10), 
						cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
		
		# 绘制级别区域
		if "grade" in panel_rois:
			grade_roi = panel_rois["grade"]
			x2, y2, w2, h2 = grade_roi
			cv2.rectangle(preview, (x2, y2), (x2 + w2, y2 + h2), color, 2)
			cv2.putText(preview, f"{panel_name}_级别", (x2, y2 - 10), 
						cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
	
	return preview

def save_roi_preview(img: np.ndarray, rois: Dict[str, Dict[str, list]]) -> str:
	"""保存ROI预览图"""
	# 创建预览图
	preview = create_roi_preview(img, rois)
	
	# 生成文件名
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	filename = f"roi_preview_{timestamp}.png"
	
	# 确保目录存在
	preview_dir = "../data/roi_previews"
	os.makedirs(preview_dir, exist_ok=True)
	
	# 保存文件
	filepath = os.path.join(preview_dir, filename)
	cv2.imwrite(filepath, preview)
	
	return filepath

def load_rois() -> Dict[str, Dict[str, list]]:
	"""加载ROI配置"""
	rois_file = "../data/rois.json"
	
	if not os.path.exists(rois_file):
		print(f"❌ ROI配置文件不存在: {rois_file}")
		print("请先运行 python tools/calibrate_rois.py 生成ROI配置")
		return {}
	
	try:
		with open(rois_file, "r", encoding="utf-8") as f:
			rois = json.load(f)
		print(f"✓ 成功加载ROI配置，包含 {len(rois)} 个板块")
		return rois
	except Exception as e:
		print(f"❌ 加载ROI配置失败: {e}")
		return {}

def main():
	"""主函数"""
	print("=== ROI预览查看工具 ===")
	print("此工具会基于现有ROI配置生成带框框的预览图")
	print("请确保天狼50监控页面在前台\n")
	
	# 加载ROI配置
	rois = load_rois()
	if not rois:
		return
	
	# 截图
	print("正在截图...")
	with mss() as sct:
		img = grab_fullscreen(sct)
		print(f"截图完成，图像尺寸: {img.shape}")
	
	# 生成预览图
	print("正在生成ROI预览图...")
	preview_path = save_roi_preview(img, rois)
	print(f"✓ ROI预览图已保存: {preview_path}")
	
	# 显示预览图
	print("\n正在显示ROI预览图...")
	cv2.namedWindow("ROI预览", cv2.WINDOW_NORMAL)
	cv2.resizeWindow("ROI预览", 1280, 720)
	cv2.moveWindow("ROI预览", 200, 200)
	
	preview = create_roi_preview(img, rois)
	cv2.imshow("ROI预览", preview)
	
	print("\n预览说明:")
	print("- 每个板块用不同颜色的框框标出")
	print("- 框框位置基于当前ROI配置")
	print("- 请检查框框是否准确框选了目标区域")
	print("- 按任意键关闭预览窗口")
	
	cv2.waitKey(0)
	cv2.destroyAllWindows()
	
	print("\n=== 预览完成 ===")
	print("1. ROI预览图已保存到 ../data/roi_previews/")
	print("2. 如果框框位置不准确，请运行 python tools/calibrate_rois.py 重新校准")
	print("3. 如果框框位置准确，可以运行监控程序测试识别效果")

if __name__ == "__main__":
	main()
