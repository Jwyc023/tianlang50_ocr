#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单调试脚本 - 直接分析CSV和截图
"""

import cv2
import numpy as np
import pytesseract
import json
import os
import pandas as pd

def main():
    """主函数"""
    print("=== 简单调试脚本 ===")
    
    # 检查当前工作目录
    print(f"当前工作目录: {os.getcwd()}")
    
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
    
    print("✓ 所有文件都存在")
    
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        print(f"✓ CSV读取成功，总记录数: {len(df)}")
        print(f"列名: {list(df.columns)}")
    except Exception as e:
        print(f"❌ CSV读取失败: {e}")
        return
    
    # 查找创业板指级别为空的记录
    empty_mask = df['创业板指_级别'].isna() | (df['创业板指_级别'] == '')
    empty_records = df[empty_mask]
    
    print(f"找到 {len(empty_records)} 条创业板指级别为空的记录")
    
    if len(empty_records) > 0:
        print(f"\n开始分析所有 {len(empty_records)} 条创业板指级别为空的记录...")
        
        # 分析所有空记录
        for idx, (_, record) in enumerate(empty_records.iterrows()):
            print(f"\n--- 分析记录 {idx+1}/{len(empty_records)} ---")
            print(f"时间: {record['timestamp']}")
            
            screenshot_file = record['截图文件']
            if screenshot_file and screenshot_file != 'N/A':
                screenshot_path = os.path.join(screenshots_dir, os.path.basename(screenshot_file))
                print(f"截图路径: {screenshot_path}")
                
                if os.path.exists(screenshot_path):
                    debug_screenshot(screenshot_path, idx+1)
                else:
                    print(f"❌ 截图文件不存在: {screenshot_path}")
            else:
                print("❌ 没有截图文件信息")
    else:
        print("✓ 没有找到空的记录")

def debug_screenshot(screenshot_path, record_num=1):
    """调试截图"""
    print(f"\n🔍 调试截图 {record_num}: {screenshot_path}")
    
    # 加载ROI配置
    try:
        with open("data/rois.json", "r", encoding="utf-8") as f:
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
    
    # 创建调试目录
    debug_dir = "data/debug_roi_annotations"
    os.makedirs(debug_dir, exist_ok=True)
    
    # 标注所有ROI区域
    annotated_img = img.copy()
    
    # 定义颜色
    colors = [
        (0, 0, 255),    # 红色
        (0, 255, 0),    # 绿色
        (255, 0, 0),    # 蓝色
        (255, 255, 0),  # 青色
        (255, 0, 255),  # 洋红
        (0, 255, 255),  # 黄色
        (128, 0, 128),  # 紫色
        (255, 165, 0),  # 橙色
    ]
    
    panel_names = ["中证1000", "中证500", "沪深300", "上证50", "上证指数", "深证成指", "科创50", "创业板指"]
    
    for i, panel_name in enumerate(panel_names):
        if panel_name in rois:
            panel_rois = rois[panel_name]
            
            # 标注主力等级ROI
            if "power" in panel_rois:
                power_roi = panel_rois["power"]
                x, y, w, h = power_roi[0], power_roi[1], power_roi[2], power_roi[3]
                color = colors[i % len(colors)]
                cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(annotated_img, f"{panel_name}_主力等级", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 标注级别ROI
            if "grade" in panel_rois:
                grade_roi = panel_rois["grade"]
                x, y, w, h = grade_roi[0], grade_roi[1], grade_roi[2], grade_roi[3]
                color = colors[(i + 1) % len(colors)]
                cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(annotated_img, f"{panel_name}_级别", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # 保存标注后的图像
    annotated_file = os.path.join(debug_dir, f"roi_annotated_record{record_num}_{os.path.basename(screenshot_path)}")
    cv2.imwrite(annotated_file, annotated_img)
    print(f"✓ 已保存ROI标注图像: {annotated_file}")
    
    # 特别关注创业板指的级别ROI
    if "创业板指" in rois and "grade" in rois["创业板指"]:
        grade_roi = rois["创业板指"]["grade"]
        x, y, w, h = grade_roi[0], grade_roi[1], grade_roi[2], grade_roi[3]
        
        print(f"创业板指级别ROI: ({x}, {y}, {w}, {h})")
        
        # 提取创业板指级别区域
        grade_region = img[y:y+h, x:x+w]
        
        # 保存创业板指级别区域
        grade_file = os.path.join(debug_dir, f"创业板指_级别_record{record_num}_{os.path.basename(screenshot_path)}")
        cv2.imwrite(grade_file, grade_region)
        print(f"✓ 已保存创业板指级别区域: {grade_file}")
        
        # 测试OCR识别
        print(f"\n=== OCR测试 ===")
        
        # 预处理
        gray = cv2.cvtColor(grade_region, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 保存预处理后的图像
        proc_file = os.path.join(debug_dir, f"创业板指_级别_processed_record{record_num}_{os.path.basename(screenshot_path)}")
        cv2.imwrite(proc_file, thr)
        print(f"✓ 已保存预处理图像: {proc_file}")
        
        # OCR测试
        configs = [
            ("单词模式", "--psm 8 -l eng+chi_sim"),
            ("单字符模式", "--psm 10 -l eng+chi_sim"),
            ("单行模式", "--psm 7 -l eng+chi_sim"),
        ]
        
        for config_name, cfg in configs:
            try:
                text = pytesseract.image_to_string(thr, config=cfg).strip()
                print(f"  {config_name}: '{text}'")
            except Exception as e:
                print(f"  {config_name}: OCR失败 - {e}")
    
    print(f"\n✅ 调试完成！")
    print(f"📁 调试文件保存在: {debug_dir}/")
    print(f"请查看ROI标注图像，检查创业板指级别区域是否正确框选了'-A'字符")

if __name__ == "__main__":
    main()
