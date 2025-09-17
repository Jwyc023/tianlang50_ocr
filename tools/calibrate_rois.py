import json
import time
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
	monitor = sct.monitors[0]
	img = np.array(sct.grab(monitor))
	return img[:, :, :3]


def show_info(img: np.ndarray, text: str) -> None:
	view = img.copy()
	cv2.putText(view, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
	cv2.imshow("calibrate", view)


def select_roi(img: np.ndarray, prompt: str) -> Tuple[int, int, int, int]:
	show_info(img, prompt)
	print(f"正在等待框选: {prompt}")
	print("请确保 'calibrate' 窗口在前台，然后拖拽鼠标框选区域...")
	
	# 确保窗口可见并置顶
	cv2.setWindowProperty("calibrate", cv2.WND_PROP_TOPMOST, 1)
	cv2.waitKey(100)  # 给窗口时间显示
	
	roi = cv2.selectROI("calibrate", img, showCrosshair=True, fromCenter=False)
	
	# 检查是否选择了有效区域
	if roi[2] <= 0 or roi[3] <= 0:
		print("警告: 未选择有效区域，请重新选择")
		return select_roi(img, prompt)
	
	x, y, w, h = roi
	print(f"已选择区域: x={x}, y={y}, w={w}, h={h}")
	return int(x), int(y), int(w), int(h)


def create_roi_preview(img: np.ndarray, rois: Dict[str, Dict[str, Tuple[int, int, int, int]]]) -> np.ndarray:
	"""创建ROI预览图，用不同颜色的框框标出每个区域"""
	preview = img.copy()
	
	# 定义颜色 (BGR格式)
	colors = [
		(0, 255, 0),    # 绿色 - 主力等级
		(0, 0, 255),    # 红色 - 级别
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
		power_roi = panel_rois["power"]
		x1, y1, w1, h1 = power_roi
		cv2.rectangle(preview, (x1, y1), (x1 + w1, y1 + h1), color, 2)
		cv2.putText(preview, f"{panel_name}_主力", (x1, y1 - 10), 
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
		
		# 绘制级别区域
		grade_roi = panel_rois["grade"]
		x2, y2, w2, h2 = grade_roi
		cv2.rectangle(preview, (x2, y2), (x2 + w2, y2 + h2), color, 2)
		cv2.putText(preview, f"{panel_name}_级别", (x2, y2 - 10), 
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
	
	return preview

def save_roi_preview(img: np.ndarray, rois: Dict[str, Dict[str, Tuple[int, int, int, int]]]) -> str:
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

def main() -> None:
	print("说明：")
	print("1) 将监控页面置于前台，覆盖到屏幕上以便完整截图。")
	print("2) 程序会提示依次框选8个板块的两个区域：'主力等级' 与 '级别'。")
	print("3) 按回车确认，按Esc可取消当前选择重新框选。")
	print("4) 如果看不到框选界面，请检查是否有 'calibrate' 窗口出现。")
	print("5) 校准完成后会自动生成带框框的预览图，方便验证ROI是否准确。\n")

	input("按回车键开始截图和框选...")

	rois: Dict[str, Dict[str, Tuple[int, int, int, int]]] = {}

	with mss() as sct:
		print("正在截图...")
		time.sleep(0.8)
		img = grab_fullscreen(sct)
		print(f"截图完成，图像尺寸: {img.shape}")
		
		cv2.namedWindow("calibrate", cv2.WINDOW_NORMAL)
		cv2.resizeWindow("calibrate", 1280, 720)
		cv2.moveWindow("calibrate", 100, 100)  # 确保窗口在可见位置
		print("已创建 'calibrate' 窗口，请确保窗口可见")

		for i, name in enumerate(PANEL_NAMES, 1):
			print(f"\n=== 第 {i}/8 个板块: {name} ===")
			
			prompt1 = f"请框选【{name}】的 '主力等级' 数值区域，然后按Enter确认"
			x1, y1, w1, h1 = select_roi(img, prompt1)

			prompt2 = f"请框选【{name}】的 '级别' 文本区域，然后按Enter确认"
			x2, y2, w2, h2 = select_roi(img, prompt2)

			rois[name] = {
				"power": [int(x1), int(y1), int(w1), int(h1)],
				"grade": [int(x2), int(y2), int(w2), int(h2)],
			}
			print(f"✓ 已记录 {name}")
			show_info(img, f"已记录 {name} ({i}/8)，继续下一项……")
			cv2.waitKey(500)

		cv2.destroyAllWindows()

	# 保存ROI配置
	with open("../data/rois.json", "w", encoding="utf-8") as f:
		json.dump(rois, f, ensure_ascii=False, indent=2)
	print("✓ 已保存到 ../data/rois.json")
	
	# 生成并保存ROI预览图
	print("正在生成ROI预览图...")
	preview_path = save_roi_preview(img, rois)
	print(f"✓ ROI预览图已保存: {preview_path}")
	
	# 显示预览图
	print("\n正在显示ROI预览图，请检查框框位置是否准确...")
	cv2.namedWindow("ROI预览", cv2.WINDOW_NORMAL)
	cv2.resizeWindow("ROI预览", 1280, 720)
	cv2.moveWindow("ROI预览", 200, 200)
	
	preview = create_roi_preview(img, rois)
	cv2.imshow("ROI预览", preview)
	
	print("预览说明:")
	print("- 每个板块用不同颜色的框框标出")
	print("- 绿色框：主力等级区域")
	print("- 红色框：级别区域")
	print("- 按任意键关闭预览窗口")
	
	cv2.waitKey(0)
	cv2.destroyAllWindows()
	
	print("\n=== 校准完成 ===")
	print("1. ROI配置已保存到 ../data/rois.json")
	print("2. ROI预览图已保存到 ../data/roi_previews/")
	print("3. 如果框框位置不准确，请重新运行校准程序")
	print("4. 现在可以运行监控程序测试识别效果")


if __name__ == "__main__":
	main()

