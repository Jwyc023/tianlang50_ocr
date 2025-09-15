#!/usr/bin/env python3
"""
简单测试脚本 - 用于诊断问题
"""

import json
import os

def main():
    print("=== 简单测试脚本 ===")
    
    # 检查文件是否存在
    print("1. 检查文件...")
    files_to_check = ["rois.json", "calibrate_rois.py", "monitor.py", "test_ocr.py"]
    for file in files_to_check:
        if os.path.exists(file):
            print(f"  ✓ {file} 存在")
        else:
            print(f"  ✗ {file} 不存在")
    
    # 检查rois.json内容
    print("\n2. 检查rois.json...")
    try:
        with open("data/rois.json", "r", encoding="utf-8") as f:
            rois = json.load(f)
        print(f"  ✓ rois.json 加载成功，包含 {len(rois)} 个板块")
        
        for name in rois:
            power_roi = rois[name]["power"]
            grade_roi = rois[name]["grade"]
            print(f"  - {name}: power={power_roi}, grade={grade_roi}")
            
    except Exception as e:
        print(f"  ✗ rois.json 加载失败: {e}")
    
    # 检查依赖
    print("\n3. 检查依赖...")
    try:
        import cv2
        print("  ✓ opencv-python 已安装")
    except ImportError:
        print("  ✗ opencv-python 未安装")
    
    try:
        import pytesseract
        print("  ✓ pytesseract 已安装")
    except ImportError:
        print("  ✗ pytesseract 未安装")
    
    try:
        from mss import mss
        print("  ✓ mss 已安装")
    except ImportError:
        print("  ✗ mss 未安装")
    
    # 测试基本功能
    print("\n4. 测试基本功能...")
    try:
        import cv2
        import numpy as np
        from mss import mss
        
        with mss() as sct:
            monitor = sct.monitors[0]
            img = np.array(sct.grab(monitor))
            print(f"  ✓ 截图成功，图像尺寸: {img.shape}")
            
            # 测试保存图像
            cv2.imwrite("test_screenshot.png", img[:, :, :3])
            print("  ✓ 图像保存成功: test_screenshot.png")
            
    except Exception as e:
        print(f"  ✗ 基本功能测试失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("如果所有项目都显示 ✓，那么问题可能在OCR识别部分")
    print("如果看到 ✗，请先解决对应的问题")

if __name__ == "__main__":
    main()
