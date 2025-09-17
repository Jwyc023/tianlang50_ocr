
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI校准工具 - 手动调整ROI区域
"""

import cv2
import numpy as np
import json
import os
from mss import mss

class ROICalibrator:
    def __init__(self):
        self.roi_file = "data/rois.json"
        self.current_roi = None
        self.img = None
        self.display_img = None
        
    def load_current_roi(self):
        """加载当前ROI配置"""
        if os.path.exists(self.roi_file):
            with open(self.roi_file, "r", encoding="utf-8") as f:
                rois = json.load(f)
            if "创业板指" in rois and "grade" in rois["创业板指"]:
                self.current_roi = rois["创业板指"]["grade"]
                return True
        return False
        
    def capture_screen(self):
        """截图"""
        with mss() as sct:
            monitor = sct.monitors[0]
            self.img = np.array(sct.grab(monitor))
            self.img = self.img[:, :, :3]
            
    def draw_roi(self, roi):
        """在图像上绘制ROI"""
        if roi is None:
            return self.img.copy()
            
        x, y, w, h = roi
        display_img = self.img.copy()
        
        # 绘制ROI矩形
        cv2.rectangle(display_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # 绘制ROI信息
        cv2.putText(display_img, f"ROI: ({x}, {y}, {w}, {h})", 
                    (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return display_img
        
    def show_roi_preview(self):
        """显示ROI预览"""
        if self.current_roi is None:
            print("❌ 没有找到当前ROI配置")
            return
            
        self.capture_screen()
        display_img = self.draw_roi(self.current_roi)
        
        # 显示图像
        cv2.imshow("ROI预览 - 按ESC退出", display_img)
        
        print("当前ROI预览已显示")
        print("按ESC键退出预览")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC键
                break
                
        cv2.destroyAllWindows()
        
    def interactive_calibration(self):
        """交互式校准"""
        print("=== 交互式ROI校准 ===")
        print("使用鼠标拖拽来调整ROI区域")
        print("按ESC键退出")
        
        self.capture_screen()
        
        # 设置鼠标回调
        cv2.namedWindow("ROI校准", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("ROI校准", self.mouse_callback)
        
        # 初始化ROI
        if self.current_roi is None:
            h, w = self.img.shape[:2]
            self.current_roi = [w//4, h//4, w//2, h//2]
            
        self.update_display()
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC键
                break
            elif key == ord('s'):  # 保存
                self.save_roi()
                break
            elif key == ord('r'):  # 重置
                self.reset_roi()
                
        cv2.destroyAllWindows()
        
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.dragging = True
            self.start_x, self.start_y = x, y
            
        elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
            # 更新ROI
            x1, y1 = self.start_x, self.start_y
            x2, y2 = x, y
            
            self.current_roi = [
                min(x1, x2),
                min(y1, y2),
                abs(x2 - x1),
                abs(y2 - y1)
            ]
            
            self.update_display()
            
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
            
    def update_display(self):
        """更新显示"""
        display_img = self.draw_roi(self.current_roi)
        
        # 添加说明文字
        cv2.putText(display_img, "Drag to adjust ROI", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_img, "Press 's' to save, 'r' to reset, ESC to exit", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("ROI校准", display_img)
        
    def save_roi(self):
        """保存ROI配置"""
        if self.current_roi is None:
            return
            
        # 加载现有配置
        rois = {}
        if os.path.exists(self.roi_file):
            with open(self.roi_file, "r", encoding="utf-8") as f:
                rois = json.load(f)
                
        # 更新创业板指级别ROI
        if "创业板指" not in rois:
            rois["创业板指"] = {}
        rois["创业板指"]["grade"] = self.current_roi
        
        # 保存配置
        with open(self.roi_file, "w", encoding="utf-8") as f:
            json.dump(rois, f, ensure_ascii=False, indent=2)
            
        print(f"✓ ROI配置已保存: {self.current_roi}")
        
    def reset_roi(self):
        """重置ROI"""
        h, w = self.img.shape[:2]
        self.current_roi = [w//4, h//4, w//2, h//2]
        self.update_display()

def main():
    """主函数"""
    calibrator = ROICalibrator()
    
    print("ROI校准工具")
    print("1. 显示当前ROI预览")
    print("2. 交互式校准")
    print("3. 退出")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == "1":
        calibrator.load_current_roi()
        calibrator.show_roi_preview()
    elif choice == "2":
        calibrator.load_current_roi()
        calibrator.interactive_calibration()
    else:
        print("退出")

if __name__ == "__main__":
    main()
