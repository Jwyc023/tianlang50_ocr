#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门分析特定截图的OCR识别问题
"""

import cv2
import numpy as np
import pytesseract
import json
import os
import pandas as pd

def analyze_specific_screenshot():
    """分析特定截图"""
    print("=== 分析 fullscreen_20250915_222916.png ===")
    
    # 文件路径
    screenshot_path = "data/fast_screenshots/fullscreen_20250915_222916.png"
    rois_file = "data/rois.json"
    csv_file = "data/ticks_fast_20250915_222915.csv"
    
    # 检查文件存在性
    if not os.path.exists(screenshot_path):
        print(f"❌ 截图文件不存在: {screenshot_path}")
        return
    
    if not os.path.exists(rois_file):
        print(f"❌ ROI文件不存在: {rois_file}")
        return
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV文件不存在: {csv_file}")
        return
    
    print("✓ 所有文件都存在")
    
    # 加载ROI配置
    try:
        with open(rois_file, "r", encoding="utf-8") as f:
            rois = json.load(f)
        print("✓ ROI配置加载成功")
    except Exception as e:
        print(f"❌ ROI配置加载失败: {e}")
        return
    
    # 加载截图
    img = cv2.imread(screenshot_path)
    if img is None:
        print(f"❌ 无法加载截图: {screenshot_path}")
        return
    
    print(f"✓ 截图尺寸: {img.shape}")
    
    # 获取创业板指级别ROI
    if "创业板指" not in rois or "grade" not in rois["创业板指"]:
        print("❌ 创业板指级别ROI不存在")
        return
    
    grade_roi = rois["创业板指"]["grade"]
    x, y, w, h = grade_roi[0], grade_roi[1], grade_roi[2], grade_roi[3]
    print(f"创业板指级别ROI: ({x}, {y}, {w}, {h})")
    
    # 提取创业板指级别区域
    grade_region = img[y:y+h, x:x+w]
    print(f"级别区域尺寸: {grade_region.shape}")
    
    # 创建调试目录
    debug_dir = "data/debug_specific"
    os.makedirs(debug_dir, exist_ok=True)
    
    # 保存原始级别区域
    raw_file = os.path.join(debug_dir, "cyb_grade_raw.png")
    cv2.imwrite(raw_file, grade_region)
    print(f"✓ 已保存原始级别区域: {raw_file}")
    
    # 测试多种预处理方法
    print(f"\n=== 多种预处理方法测试 ===")
    
    preprocessing_methods = [
        ("original", grade_region),
        ("gray", cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY)),
        ("gray_2x", cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2)),
        ("gray_3x", cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3)),
        ("otsu", cv2.threshold(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
        ("adaptive", cv2.adaptiveThreshold(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("adaptive_2x", cv2.adaptiveThreshold(cv2.resize(cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
    ]
    
    ocr_configs = [
        ("单词模式", "--psm 8 -l eng+chi_sim"),
        ("单字符模式", "--psm 10 -l eng+chi_sim"),
        ("单行模式", "--psm 7 -l eng+chi_sim"),
        ("单字符模式-仅英文", "--psm 10 -l eng"),
        ("单词模式-仅英文", "--psm 8 -l eng"),
    ]
    
    results = []
    
    for method_name, processed_img in preprocessing_methods:
        print(f"\n--- {method_name} ---")
        
        # 保存预处理后的图像
        method_file = os.path.join(debug_dir, f"cyb_grade_{method_name}.png")
        cv2.imwrite(method_file, processed_img)
        print(f"✓ 已保存: {method_file}")
        
        # 测试各种OCR配置
        for config_name, config in ocr_configs:
            try:
                text = pytesseract.image_to_string(processed_img, config=config).strip()
                print(f"  {config_name}: '{text}'")
                
                # 记录结果
                results.append({
                    'method': method_name,
                    'config': config_name,
                    'text': text,
                    'file': method_file
                })
                
            except Exception as e:
                print(f"  {config_name}: OCR失败 - {e}")
    
    # 分析CSV文件中的对应记录
    print(f"\n=== CSV文件分析 ===")
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        # 查找对应时间戳的记录
        target_time = "2025-09-15 22:29:16"  # 对应截图时间
        matching_records = df[df['timestamp'] == target_time]
        
        if len(matching_records) > 0:
            record = matching_records.iloc[0]
            print(f"找到对应记录: {record['timestamp']}")
            print(f"创业板指级别: '{record['创业板指_级别']}'")
            print(f"创业板指主力等级: '{record['创业板指_主力等级']}'")
            print(f"结论: '{record['结论']}'")
        else:
            print(f"❌ 未找到时间戳为 {target_time} 的记录")
            print(f"CSV中的时间戳示例: {df['timestamp'].head().tolist()}")
            
    except Exception as e:
        print(f"❌ CSV分析失败: {e}")
    
    # 总结OCR结果
    print(f"\n=== OCR结果总结 ===")
    print("所有OCR识别结果:")
    for result in results:
        if result['text']:  # 只显示非空结果
            print(f"  {result['method']} + {result['config']}: '{result['text']}'")
    
    # 检查是否有识别到-A的结果
    negative_a_results = [r for r in results if '-A' in r['text'] or 'A' in r['text']]
    if negative_a_results:
        print(f"\n✓ 找到识别到'A'的结果:")
        for result in negative_a_results:
            print(f"  {result['method']} + {result['config']}: '{result['text']}'")
    else:
        print(f"\n❌ 没有找到识别到'A'的结果")
    
    print(f"\n✅ 分析完成！")
    print(f"📁 调试文件保存在: {debug_dir}/")
    print(f"请查看生成的图像文件，对比OCR识别结果")

if __name__ == "__main__":
    analyze_specific_screenshot()
