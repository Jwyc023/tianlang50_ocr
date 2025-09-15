#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同字母的OCR识别效果
"""

import cv2
import numpy as np
import pytesseract
import json
import os
import pandas as pd
import glob

def test_letter_recognition():
    """测试不同字母的OCR识别效果"""
    print("=== 测试不同字母的OCR识别效果 ===")
    
    # 检查文件
    csv_file = "data/ticks_fast_20250915_231313.csv"
    rois_file = "data/rois.json"
    screenshots_dir = "data/fast_screenshots"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV文件不存在: {csv_file}")
        return
    
    if not os.path.exists(rois_file):
        print(f"❌ ROI文件不存在: {rois_file}")
        return
    
    if not os.path.exists(screenshots_dir):
        print(f"❌ 截图目录不存在: {screenshots_dir}")
        return
    
    # 加载ROI配置
    try:
        with open(rois_file, "r", encoding="utf-8") as f:
            rois = json.load(f)
        print("✓ ROI配置加载成功")
    except Exception as e:
        print(f"❌ ROI配置加载失败: {e}")
        return
    
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        print(f"✓ CSV读取成功，总记录数: {len(df)}")
    except Exception as e:
        print(f"❌ CSV读取失败: {e}")
        return
    
    # 查找创业板指级别为空的记录
    empty_mask = df['创业板指_级别'].isna() | (df['创业板指_级别'] == '')
    empty_records = df[empty_mask]
    
    print(f"找到 {len(empty_records)} 条创业板指级别为空的记录")
    
    if len(empty_records) == 0:
        print("✓ 没有找到空的记录")
        return
    
    # 创建调试目录
    debug_dir = "data/debug_letter_recognition"
    os.makedirs(debug_dir, exist_ok=True)
    
    # 分析每条空记录
    for idx, (_, record) in enumerate(empty_records.head(5).iterrows()):  # 只分析前5条
        print(f"\n--- 分析记录 {idx+1} ---")
        print(f"时间: {record['timestamp']}")
        
        screenshot_file = record['截图文件']
        if screenshot_file and screenshot_file != 'N/A':
            screenshot_path = os.path.join(screenshots_dir, os.path.basename(screenshot_file))
            print(f"截图: {screenshot_path}")
            
            if os.path.exists(screenshot_path):
                analyze_screenshot(screenshot_path, rois, debug_dir, idx+1)
            else:
                print(f"❌ 截图文件不存在: {screenshot_path}")
        else:
            print("❌ 没有截图文件信息")

def analyze_screenshot(screenshot_path, rois, debug_dir, record_num):
    """分析特定截图"""
    print(f"🔍 分析截图: {screenshot_path}")
    
    # 加载截图
    img = cv2.imread(screenshot_path)
    if img is None:
        print(f"❌ 无法加载截图: {screenshot_path}")
        return
    
    # 获取创业板指级别ROI
    if "创业板指" not in rois or "grade" not in rois["创业板指"]:
        print("❌ 创业板指级别ROI不存在")
        return
    
    grade_roi = rois["创业板指"]["grade"]
    x, y, w, h = grade_roi[0], grade_roi[1], grade_roi[2], grade_roi[3]
    
    # 提取创业板指级别区域
    grade_region = img[y:y+h, x:x+w]
    
    # 保存原始区域
    raw_file = os.path.join(debug_dir, f"cyb_grade_raw_record{record_num}.png")
    cv2.imwrite(raw_file, grade_region)
    print(f"✓ 已保存原始区域: {raw_file}")
    
    # 测试多种预处理方法
    preprocessing_methods = [
        ("original", grade_region),
        ("gray", cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY)),
        ("gray_2x", cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2)),
        ("gray_3x", cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3)),
        ("otsu", cv2.threshold(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
        ("adaptive", cv2.adaptiveThreshold(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("adaptive_2x", cv2.adaptiveThreshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("adaptive_3x", cv2.adaptiveThreshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
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
    ]
    
    print(f"\n=== OCR测试结果 ===")
    
    best_results = []
    
    for method_name, processed_img in preprocessing_methods:
        print(f"\n--- {method_name} ---")
        
        # 保存预处理后的图像
        method_file = os.path.join(debug_dir, f"cyb_grade_{method_name}_record{record_num}.png")
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
    else:
        print(f"\n❌ 没有找到有效的识别结果")
    
    print(f"\n📁 调试文件保存在: {debug_dir}/")

if __name__ == "__main__":
    test_letter_recognition()
