#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速调试特定截图
"""

import cv2
import numpy as np
import pytesseract
import json
import os

def debug_specific_file():
    """调试特定截图文件"""
    screenshot_path = "../data/fast_screenshots/fullscreen_20250915_221245.png"
    panel_name = "中证1000"
    
    print(f"=== 调试截图: {screenshot_path} ===")
    
    if not os.path.exists(screenshot_path):
        print(f"❌ 截图文件不存在: {screenshot_path}")
        return
    
    # 加载ROI配置
    try:
        with open("../data/rois.json", "r", encoding="utf-8") as f:
            rois = json.load(f)
    except Exception as e:
        print(f"❌ 加载ROI配置失败: {e}")
        return
    
    if panel_name not in rois:
        print(f"❌ 板块 {panel_name} 不在ROI配置中")
        return
    
    # 加载截图
    img = cv2.imread(screenshot_path)
    if img is None:
        print(f"❌ 无法加载截图: {screenshot_path}")
        return
    
    print(f"✓ 截图尺寸: {img.shape}")
    
    # 获取ROI坐标
    x1, y1, w1, h1 = rois[panel_name]["power"]
    x2, y2, w2, h2 = rois[panel_name]["grade"]
    
    print(f"✓ {panel_name} ROI坐标:")
    print(f"  主力等级: ({x1}, {y1}, {w1}, {h1})")
    print(f"  级别: ({x2}, {y2}, {w2}, {h2})")
    
    # 裁剪ROI区域
    crop_power = img[y1:y1+h1, x1:x1+w1]
    crop_grade = img[y2:y2+h2, x2:x2+w2]
    
    print(f"✓ 裁剪区域尺寸:")
    print(f"  主力等级: {crop_power.shape}")
    print(f"  级别: {crop_grade.shape}")
    
    # 保存原始裁剪图像
    cv2.imwrite(f"{panel_name}_power_raw.png", crop_power)
    cv2.imwrite(f"{panel_name}_grade_raw.png", crop_grade)
    print(f"✓ 已保存原始裁剪图像")
    
    # 预处理
    def preprocess(img, is_grade=False):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if is_grade:
            gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)
            _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
            thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return thr
    
    pp = preprocess(crop_power, is_grade=False)
    pg = preprocess(crop_grade, is_grade=True)
    
    # 保存预处理图像
    cv2.imwrite(f"{panel_name}_power_proc.png", pp)
    cv2.imwrite(f"{panel_name}_grade_proc.png", pg)
    print(f"✓ 已保存预处理图像")
    
    # OCR识别测试
    print(f"\n=== OCR识别测试 ===")
    
    # 级别识别（多种配置测试）
    configs = [
        ("单词模式", f"--psm 8 -l eng --oem 3"),
        ("单字符模式", f"--psm 10 -l eng --oem 3"),
        ("单行模式", f"--psm 7 -l eng --oem 3"),
        ("单字符块", f"--psm 6 -l eng --oem 3"),
        ("原始模式", f"--psm 13 -l eng --oem 3"),
        ("单字符原始", f"--psm 10 -l eng --oem 1"),
    ]
    
    print(f"级别识别测试:")
    for config_name, cfg in configs:
        text = pytesseract.image_to_string(pg, config=cfg).strip()
        print(f"  {config_name}: '{text}'")
    
    # 规范化测试
    def normalize_grade(text):
        t = text.upper().replace(" ", "").replace("- ", "-").replace("—", "-")
        t = t.replace("O", "0").replace("o", "0")
        
        sign = ""
        if t.startswith("-"):
            sign = "-"
            t = t[1:]
        
        grade = ""
        if "AAA" in t or t.startswith("3A"):
            grade = "AAA"
        elif "AA" in t or t.startswith("2A"):
            grade = "AA"
        elif t.startswith("A") or "A" in t:
            grade = "A"
        elif t.startswith("B") or "B" in t:
            grade = "B"
        elif t.startswith("C") or "C" in t:
            grade = "C"
        else:
            return ""
        
        return sign + grade
    
    print(f"\n规范化结果:")
    for config_name, cfg in configs:
        text = pytesseract.image_to_string(pg, config=cfg).strip()
        normalized = normalize_grade(text)
        print(f"  {config_name}: '{text}' -> '{normalized}'")
    
    print(f"\n✅ 调试完成！")
    print(f"请查看生成的图像文件分析问题")

if __name__ == "__main__":
    debug_specific_file()

