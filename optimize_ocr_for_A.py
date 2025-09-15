#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化OCR识别字母A
"""

import cv2
import numpy as np
import pytesseract
import json
import os
from mss import mss

def optimize_ocr_for_A():
    """优化OCR识别字母A"""
    print("=== 优化OCR识别字母A ===")
    
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
    
    # 截图
    print("正在截图...")
    with mss() as sct:
        monitor = sct.monitors[0]
        img = np.array(sct.grab(monitor))
        img = img[:, :, :3]
    
    # 提取创业板指级别区域
    grade_region = img[y:y+h, x:x+w]
    
    # 创建调试目录
    debug_dir = "data/debug_ocr_optimization"
    os.makedirs(debug_dir, exist_ok=True)
    
    # 保存原始区域
    raw_file = os.path.join(debug_dir, "cyb_grade_raw.png")
    cv2.imwrite(raw_file, grade_region)
    print(f"✓ 已保存原始区域: {raw_file}")
    
    # 测试多种预处理方法
    preprocessing_methods = [
        ("original", grade_region),
        ("gray", cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY)),
        ("gray_2x", cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2)),
        ("gray_3x", cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3)),
        ("gray_4x", cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=4, fy=4)),
        ("otsu", cv2.threshold(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
        ("otsu_2x", cv2.threshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
        ("adaptive", cv2.adaptiveThreshold(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("adaptive_2x", cv2.adaptiveThreshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("adaptive_3x", cv2.adaptiveThreshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("adaptive_4x", cv2.adaptiveThreshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=4, fy=4), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("morphology", cv2.morphologyEx(cv2.adaptiveThreshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2), cv2.MORPH_CLOSE, np.ones((2,2), np.uint8))),
    ]
    
    # 测试多种OCR配置
    ocr_configs = [
        ("单词模式_中英文", "--psm 8 -l eng+chi_sim"),
        ("单字符模式_中英文", "--psm 10 -l eng+chi_sim"),
        ("单行模式_中英文", "--psm 7 -l eng+chi_sim"),
        ("单字符模式_仅英文", "--psm 10 -l eng"),
        ("单词模式_仅英文", "--psm 8 -l eng"),
        ("单字符模式_数字字母", "--psm 10 -l eng --oem 3"),
        ("单字符模式_高精度", "--psm 10 -l eng --oem 1"),
        ("单字符模式_默认", "--psm 10"),
        ("单字符模式_数字", "--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ-"),
    ]
    
    print(f"\n=== OCR优化测试 ===")
    
    best_results = []
    
    for method_name, processed_img in preprocessing_methods:
        print(f"\n--- {method_name} ---")
        
        # 保存预处理后的图像
        method_file = os.path.join(debug_dir, f"cyb_grade_{method_name}.png")
        cv2.imwrite(method_file, processed_img)
        
        # 测试各种OCR配置
        for config_name, config in ocr_configs:
            try:
                text = pytesseract.image_to_string(processed_img, config=config).strip()
                print(f"  {config_name}: '{text}'")
                
                # 记录最佳结果
                if text and ('A' in text or 'B' in text or 'C' in text):
                    best_results.append({
                        'method': method_name,
                        'config': config_name,
                        'text': text,
                        'file': method_file
                    })
                
            except Exception as e:
                print(f"  {config_name}: OCR失败 - {e}")
    
    # 总结最佳结果
    if best_results:
        print(f"\n=== 最佳识别结果 ===")
        for result in best_results:
            print(f"  {result['method']} + {result['config']}: '{result['text']}'")
        
        # 推荐最佳配置
        best_result = best_results[0]
        print(f"\n=== 推荐配置 ===")
        print(f"预处理方法: {best_result['method']}")
        print(f"OCR配置: {best_result['config']}")
        print(f"识别结果: '{best_result['text']}'")
        
    else:
        print(f"\n❌ 没有找到有效的识别结果")
        print(f"建议:")
        print(f"1. 检查ROI区域是否正确框选了'-A'字符")
        print(f"2. 尝试调整ROI区域大小")
        print(f"3. 检查字体是否清晰")
    
    print(f"\n📁 调试文件保存在: {debug_dir}/")

if __name__ == "__main__":
    optimize_ocr_for_A()
