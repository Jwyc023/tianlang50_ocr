#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时对比OCR识别结果
"""

import cv2
import numpy as np
import pytesseract
import json
import os
import time
from mss import mss

def real_time_compare():
    """实时对比OCR识别结果"""
    print("=== 实时对比OCR识别结果 ===")
    
    # 检查文件
    rois_file = "data/rois.json"
    if not os.path.exists(rois_file):
        print(f"❌ ROI文件不存在: {rois_file}")
        return
    
    # 加载ROI配置
    try:
        with open(rois_file, "r", encoding="utf-8") as f:
            rois = json.load(f)
        print("✓ ROI配置加载成功")
    except Exception as e:
        print(f"❌ ROI配置加载失败: {e}")
        return
    
    # 获取创业板指级别ROI
    if "创业板指" not in rois or "grade" not in rois["创业板指"]:
        print("❌ 创业板指级别ROI不存在")
        return
    
    grade_roi = rois["创业板指"]["grade"]
    x, y, w, h = grade_roi[0], grade_roi[1], grade_roi[2], grade_roi[3]
    print(f"创业板指级别ROI: ({x}, {y}, {w}, {h})")
    
    # 创建调试目录
    debug_dir = "data/debug_real_time"
    os.makedirs(debug_dir, exist_ok=True)
    
    print(f"\n=== 开始实时监控（按Ctrl+C停止）===")
    
    try:
        with mss() as sct:
            monitor = sct.monitors[0]
            count = 0
            
            while True:
                count += 1
                current_time = time.strftime("%H:%M:%S")
                
                # 截图
                img = np.array(sct.grab(monitor))
                img = img[:, :, :3]
                
                # 提取创业板指级别区域
                grade_region = img[y:y+h, x:x+w]
                
                # 保存截图（每10次保存一次）
                if count % 10 == 0:
                    screenshot_file = os.path.join(debug_dir, f"cyb_grade_{current_time.replace(':', '_')}.png")
                    cv2.imwrite(screenshot_file, grade_region)
                    print(f"✓ 已保存截图: {screenshot_file}")
                
                # 测试两种OCR配置
                configs = [
                    ("PSM8_单词模式", "--psm 8 -l eng+chi_sim"),
                    ("PSM10_单字符模式", "--psm 10 -l eng+chi_sim"),
                ]
                
                results = []
                for config_name, config in configs:
                    try:
                        text = pytesseract.image_to_string(grade_region, config=config).strip()
                        results.append(f"{config_name}: '{text}'")
                    except Exception as e:
                        results.append(f"{config_name}: OCR失败 - {e}")
                
                # 显示结果
                print(f"[{current_time}] 第{count}次: {' | '.join(results)}")
                
                # 检查是否有识别到A的结果
                has_a = any('A' in result for result in results)
                if has_a:
                    print(f"🎉 发现识别到A的结果！")
                    # 保存这个特殊的截图
                    special_file = os.path.join(debug_dir, f"cyb_grade_with_A_{current_time.replace(':', '_')}.png")
                    cv2.imwrite(special_file, grade_region)
                    print(f"✓ 已保存特殊截图: {special_file}")
                
                # 等待1秒
                time.sleep(1)
                
    except KeyboardInterrupt:
        print(f"\n=== 监控结束 ===")
        print(f"📁 调试文件保存在: {debug_dir}/")
        print(f"请查看生成的截图，分析页面内容的变化")

if __name__ == "__main__":
    real_time_compare()

