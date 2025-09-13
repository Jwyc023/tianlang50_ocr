import json
import time
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


def main() -> None:
	print("说明：")
	print("1) 将监控页面置于前台，覆盖到屏幕上以便完整截图。")
	print("2) 程序会提示依次框选8个板块的两个区域：'主力等级' 与 '级别'。")
	print("3) 按回车确认，按Esc可取消当前选择重新框选。")
	print("4) 如果看不到框选界面，请检查是否有 'calibrate' 窗口出现。\n")

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

	with open("rois.json", "w", encoding="utf-8") as f:
		json.dump(rois, f, ensure_ascii=False, indent=2)
	print("已保存到 rois.json。若识别不准，可重新运行本脚本校准。")


if __name__ == "__main__":
	main()

