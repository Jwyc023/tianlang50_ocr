#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试特定时间点的OCR识别问题
"""

import cv2
import numpy as np
import pytesseract
import json
import os
from datetime import datetime
import pandas as pd

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

def fast_preprocess(img: np.ndarray, is_grade: bool = False) -> np.ndarray:
    """快速图像预处理"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if is_grade:
        # 级别：放大 + OTSU阈值
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)
        _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        # 主力等级：简单放大 + 自适应阈值
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    return thr

def fast_ocr(img: np.ndarray, psm: int = 7, is_grade: bool = False) -> str:
    """快速OCR识别"""
    # C/B/A都是英文字符，使用英文配置
    cfg = f"--psm {psm} -l eng --oem 3"
    text = pytesseract.image_to_string(img, config=cfg)
    return text.strip()

def normalize_grade(text: str) -> str:
    """规范化级别"""
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

def debug_specific_screenshot(screenshot_path: str, panel_name: str = "中证1000"):
    """调试特定截图中的OCR识别"""
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
    cv2.imwrite(f"{panel_name}_power_raw_debug.png", crop_power)
    cv2.imwrite(f"{panel_name}_grade_raw_debug.png", crop_grade)
    print(f"✓ 已保存原始裁剪图像")
    
    # 预处理
    pp = fast_preprocess(crop_power, is_grade=False)
    pg = fast_preprocess(crop_grade, is_grade=True)
    
    # 保存预处理图像
    cv2.imwrite(f"{panel_name}_power_proc_debug.png", pp)
    cv2.imwrite(f"{panel_name}_grade_proc_debug.png", pg)
    print(f"✓ 已保存预处理图像")
    
    # OCR识别
    print(f"\n=== OCR识别结果 ===")
    
    # 主力等级识别
    txt_power = fast_ocr(pp, psm=7, is_grade=False)
    print(f"主力等级原始文本: '{txt_power}'")
    
    # 级别识别（多种配置测试）
    configs = [
        ("单词模式", f"--psm 8 -l eng --oem 3"),
        ("单字符模式", f"--psm 10 -l eng --oem 3"),
        ("单行模式", f"--psm 7 -l eng --oem 3"),
        ("单字符块", f"--psm 6 -l eng --oem 3"),
        ("原始模式", f"--psm 13 -l eng --oem 3"),
    ]
    
    print(f"\n级别识别测试:")
    for config_name, cfg in configs:
        text = pytesseract.image_to_string(pg, config=cfg).strip()
        normalized = normalize_grade(text)
        print(f"  {config_name}: '{text}' -> '{normalized}'")
    
    # 显示图像
    print(f"\n=== 图像显示 ===")
    print("按任意键查看下一张图像，按ESC退出")
    
    cv2.imshow(f"{panel_name}_原始_主力等级", crop_power)
    cv2.waitKey(0)
    cv2.imshow(f"{panel_name}_预处理_主力等级", pp)
    cv2.waitKey(0)
    cv2.imshow(f"{panel_name}_原始_级别", crop_grade)
    cv2.waitKey(0)
    cv2.imshow(f"{panel_name}_预处理_级别", pg)
    cv2.waitKey(0)
    
    cv2.destroyAllWindows()

def find_screenshot_by_time(target_time: str):
    """根据时间查找对应的截图"""
    screenshot_dir = "../data/fast_screenshots"
    if not os.path.exists(screenshot_dir):
        print(f"❌ 截图目录不存在: {screenshot_dir}")
        return None
    
    # 查找最接近时间的截图
    files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
    if not files:
        print(f"❌ 截图目录为空")
        return None
    
    # 解析文件名中的时间戳
    closest_file = None
    min_diff = float('inf')
    
    for file in files:
        try:
            # 从文件名提取时间戳: fullscreen_20250915_215304.png
            time_str = file.replace('fullscreen_', '').replace('.png', '')
            file_time = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
            
            # 计算与目标时间的差值
            target_dt = datetime.strptime(target_time, '%Y-%m-%d %H:%M:%S')
            diff = abs((file_time - target_dt).total_seconds())
            
            if diff < min_diff:
                min_diff = diff
                closest_file = file
        except:
            continue
    
    if closest_file:
        screenshot_path = os.path.join(screenshot_dir, closest_file)
        print(f"✓ 找到最接近的截图: {closest_file} (时间差: {min_diff:.1f}秒)")
        return screenshot_path
    else:
        print(f"❌ 未找到合适的截图")
        return None

def main():
    """主函数"""
    print("=== OCR识别问题调试工具 ===")
    print("用于调试特定时间点的OCR识别问题")
    
    # 获取用户输入
    target_time = input("请输入目标时间 (格式: 2025-09-15 22:03:29): ").strip()
    panel_name = input("请输入要调试的板块名称 (默认: 中证1000): ").strip() or "中证1000"
    
    # 查找对应的截图
    screenshot_path = find_screenshot_by_time(target_time)
    if not screenshot_path:
        return
    
    # 调试OCR识别
    debug_specific_screenshot(screenshot_path, panel_name)
    
    print(f"\n✅ 调试完成！")
    print(f"请查看生成的调试图像文件，分析OCR识别问题")

if __name__ == "__main__":
    main()
