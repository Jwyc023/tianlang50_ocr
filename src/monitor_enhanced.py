# -*- coding: utf-8 -*-
"""
增强版监控脚本 - 集成多种OCR引擎
支持Tesseract、PaddleOCR、EasyOCR的对比和选择
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

import cv2
import numpy as np
from mss import mss

# 导入OCR替代方案
from ocr_alternatives import OCRManager, enhanced_preprocess_for_letters

# Tesseract OCR 路径配置
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

GRADES_ORDER = ["C", "B", "A", "AA", "AAA"]

# 全局锁，用于线程安全
lock = threading.Lock()

def grab_fullscreen(sct: mss) -> np.ndarray:
    """快速全屏截图"""
    monitor = sct.monitors[0]
    img = np.array(sct.grab(monitor))
    return img[:, :, :3]

def parse_power(text: str) -> float:
    """解析主力等级（从包含'主力等级：'的文本中提取数字）"""
    # 移除中文标签和空格
    t = text.replace("主力等级：", "").replace("主力等级", "").replace(" ", "")
    t = t.replace("O", "0").replace("o", "0").replace("—", "-")
    t = t.replace("+", "+").replace(",", "").replace("％", "%").replace("%", "")
    
    # 提取数字部分
    num = ""
    for ch in t:
        if ch in "+-.0123456789":
            num += ch
    
    try:
        return float(num) if num else float("nan")
    except Exception:
        return float("nan")

def normalize_grade(text: str) -> str:
    """规范化级别（从包含'级别：'的文本中提取级别）"""
    # 移除中文标签
    t = text.replace("级别：", "").replace("级别", "")
    
    # 处理各种分隔符和空格
    t = t.replace(":", "").replace("：", "").replace(" ", "").replace("\t", "")
    t = t.upper().replace("- ", "-").replace("—", "-")
    t = t.replace("O", "0").replace("o", "0")
    
    # 处理更多负号变体
    t = t.replace("一", "-").replace("_", "-").replace("—", "-")
    
    sign = ""
    # 检查各种负号位置
    if t.startswith("-") or t.startswith("一") or t.startswith("_") or t.startswith("—"):
        sign = "-"
        t = t[1:]
    elif "-" in t or "一" in t or "_" in t or "—" in t:
        # 负号在中间，提取负号后的部分
        for sep in ["-", "一", "_", "—"]:
            if sep in t:
                parts = t.split(sep, 1)
                if len(parts) == 2:
                    sign = "-"
                    t = parts[1]  # 取负号后的部分
                break
    
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

def grade_rank(grade: str) -> int:
    """级别排序"""
    if not grade:
        return -1
    g = grade[1:] if grade.startswith("-") else grade
    try:
        return GRADES_ORDER.index(g)
    except ValueError:
        return -1

def decide_signal(powers: List[float], grades: List[str]) -> str:
    """信号判断"""
    pos_cnt = sum(1 for v in powers if isinstance(v, float) and not np.isnan(v) and v > 0)
    neg_cnt = sum(1 for v in powers if isinstance(v, float) and not np.isnan(v) and v < 0)

    high_pos = sum(1 for g in grades if g and not g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))
    high_neg = sum(1 for g in grades if g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))

    if pos_cnt >= 7 and high_pos >= 3:
        return "做多"
    if neg_cnt >= 7 and high_neg >= 3:
        return "做空"
    return "观望"

def process_panel_enhanced(img: np.ndarray, name: str, rois: Dict, ocr_manager: OCRManager, 
                          ocr_engine: str = 'tesseract') -> Tuple[float, str]:
    """增强版处理单个板块（支持多种OCR引擎）"""
    try:
        x1, y1, w1, h1 = rois[name]["power"]
        x2, y2, w2, h2 = rois[name]["grade"]

        crop_power = img[y1:y1+h1, x1:x1+w1]
        crop_grade = img[y2:y2+h2, x2:x2+w2]

        # 主力等级：简单预处理
        gray_power = cv2.cvtColor(crop_power, cv2.COLOR_BGR2GRAY)
        gray_power = cv2.resize(gray_power, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        gray_power = cv2.adaptiveThreshold(gray_power, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 级别：使用增强预处理
        processed_grade = enhanced_preprocess_for_letters(crop_grade)

        # OCR识别
        txt_power = ocr_manager.recognize_text(gray_power, ocr_engine, is_grade=False)
        txt_grade = ocr_manager.recognize_text(processed_grade, ocr_engine, is_grade=True)

        # 解析结果
        val_power = parse_power(txt_power)
        val_grade = normalize_grade(txt_grade)
        
        print(f"DEBUG {name} ({ocr_engine}): 主力等级='{txt_power}'->{val_power}, 级别='{txt_grade}'->'{val_grade}'")

        return val_power, val_grade
    except Exception as e:
        print(f"处理板块 {name} 时出错: {e}")
        return float("nan"), ""

def load_rois(path: str) -> Dict[str, Dict[str, Tuple[int, int, int, int]]]:
    """加载ROI配置"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_ocr_engines_on_sample(img: np.ndarray, rois: Dict) -> None:
    """在样本图像上测试所有OCR引擎"""
    print("\n=== OCR引擎性能测试 ===")
    
    # 选择一个板块进行测试
    test_panel = PANEL_NAMES[0]
    x1, y1, w1, h1 = rois[test_panel]["power"]
    x2, y2, w2, h2 = rois[test_panel]["grade"]
    
    crop_power = img[y1:y1+h1, x1:x1+w1]
    crop_grade = img[y2:y2+h2, x2:x2+w2]
    
    # 测试主力等级识别
    print(f"\n测试板块: {test_panel}")
    print("主力等级识别测试:")
    gray_power = cv2.cvtColor(crop_power, cv2.COLOR_BGR2GRAY)
    gray_power = cv2.resize(gray_power, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    gray_power = cv2.adaptiveThreshold(gray_power, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # 测试级别识别
    print("级别识别测试:")
    processed_grade = enhanced_preprocess_for_letters(crop_grade)
    
    # 初始化OCR管理器并测试
    ocr_manager = OCRManager()
    
    if ocr_manager.engines:
        # 测试主力等级
        power_results = ocr_manager.compare_engines(gray_power, is_grade=False)
        print("\n主力等级识别结果:")
        for engine, (text, elapsed) in power_results.items():
            print(f"  {engine}: '{text}' ({elapsed:.3f}s)")
        
        # 测试级别
        grade_results = ocr_manager.compare_engines(processed_grade, is_grade=True)
        print("\n级别识别结果:")
        for engine, (text, elapsed) in grade_results.items():
            print(f"  {engine}: '{text}' ({elapsed:.3f}s)")
        
        # 保存测试图像
        cv2.imwrite("../data/test_power.png", gray_power)
        cv2.imwrite("../data/test_grade.png", processed_grade)
        print("\n✓ 测试图像已保存: test_power.png, test_grade.png")
    else:
        print("❌ 没有可用的OCR引擎")

def main():
    """主函数 - 增强版监控"""
    print("=== 增强版监控系统启动 ===")
    print("支持多种OCR引擎: Tesseract, PaddleOCR, EasyOCR")
    
    # 初始化
    rois = load_rois("../data/rois.json")
    ocr_manager = OCRManager()
    
    if not ocr_manager.engines:
        print("❌ 没有可用的OCR引擎，请先安装")
        return
    
    # 选择OCR引擎
    print(f"\n可用OCR引擎: {list(ocr_manager.engines.keys())}")
    ocr_engine = input("请选择OCR引擎 (默认: tesseract): ").strip() or "tesseract"
    
    if ocr_engine not in ocr_manager.engines:
        print(f"❌ 引擎 '{ocr_engine}' 不可用，使用默认引擎")
        ocr_engine = list(ocr_manager.engines.keys())[0]
    
    print(f"✓ 使用OCR引擎: {ocr_engine}")
    
    # 询问是否进行测试
    test_mode = input("是否先进行OCR引擎测试? (y/n, 默认: n): ").strip().lower() == 'y'
    
    out_csv = f"../data/ticks_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 创建截图保存目录
    screenshot_dir = "../data/enhanced_screenshots"
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
        print(f"✓ 创建截图目录: {screenshot_dir}")
    
    header = ["timestamp"]
    for name in PANEL_NAMES:
        header += [f"{name}_主力等级", f"{name}_级别"]
    header += ["结论", "截图文件", "OCR引擎"]

    print(f"✓ 监控 {len(rois)} 个板块")
    print(f"✓ 输出文件: {out_csv}")
    print(f"✓ 截图目录: {screenshot_dir}")
    print(f"✓ OCR引擎: {ocr_engine}")
    print("\n=== 开始监控循环 ===")

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(header)
        fcsv.flush()

        with mss() as sct:
            cycle_count = 0
            
            while True:
                cycle_start = time.time()
                cycle_count += 1
                
                # 截图
                img = grab_fullscreen(sct)
                
                # 如果是第一次循环且启用了测试模式，进行OCR测试
                if cycle_count == 1 and test_mode:
                    test_ocr_engines_on_sample(img, rois)
                    print("\n按回车键继续监控...")
                    input()
                
                # 保存完整页面截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = f"{screenshot_dir}/fullscreen_{timestamp}.png"
                cv2.imwrite(screenshot_filename, img)
                
                # 记录当前时间戳
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 并行处理所有板块
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = {}
                    for name in PANEL_NAMES:
                        future = executor.submit(process_panel_enhanced, img, name, rois, ocr_manager, ocr_engine)
                        futures[name] = future
                    
                    # 收集结果
                    powers = []
                    grades = []
                    for name in PANEL_NAMES:
                        power, grade = futures[name].result()
                        powers.append(power)
                        grades.append(grade)
                
                # 信号判断
                signal = decide_signal(powers, grades)
                
                # 写入CSV
                row = [current_time]
                for i in range(8):
                    row.append(powers[i])
                    row.append(grades[i])
                row.append(signal)
                row.append(screenshot_filename)
                row.append(ocr_engine)
                
                with lock:
                    writer.writerow(row)
                    fcsv.flush()
                
                # 时间控制
                cycle_elapsed = time.time() - cycle_start
                
                if cycle_count % 10 == 0:
                    print(f"第 {cycle_count} 次循环完成，耗时: {cycle_elapsed:.2f}秒，信号: {signal} (引擎: {ocr_engine})")
                
                sleep_time = max(0, 1.0 - cycle_elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    if cycle_count % 10 == 0:
                        print(f"⚠️  警告：处理时间过长 ({cycle_elapsed:.2f}秒)")

if __name__ == "__main__":
    main()
