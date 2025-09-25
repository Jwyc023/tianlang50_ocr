# -*- coding: utf-8 -*-
"""
高精度监控脚本 - 追求最高识别精度
不考虑处理时间，专注于识别准确率
主要特性：
1. 多引擎融合识别
2. 高级图像预处理
3. 置信度评分机制
4. 结果验证和纠错
5. 详细的调试信息
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

import cv2
import numpy as np
from mss import mss

# 导入OCR替代方案
from ocr_alternatives import OCRManager, enhanced_preprocess_for_letters

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

GRADES_ORDER = ["C", "B", "A", "AA", "AAA"]

# 全局锁，用于线程安全
lock = threading.Lock()

def grab_fullscreen(sct: mss) -> np.ndarray:
    """高质量全屏截图"""
    monitor = sct.monitors[0]
    img = np.array(sct.grab(monitor))
    return img[:, :, :3]

def ultra_preprocess_for_numbers(img: np.ndarray) -> List[np.ndarray]:
    """为数字识别提供多种预处理方案"""
    processed_images = []
    
    # 转换为灰度图
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # 方案1：高倍放大 + 自适应阈值
    gray1 = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
    gray1 = cv2.GaussianBlur(gray1, (3, 3), 0)
    thresh1 = cv2.adaptiveThreshold(gray1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    processed_images.append(thresh1)
    
    # 方案2：Otsu阈值 + 形态学操作
    gray2 = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    _, thresh2 = cv2.threshold(gray2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh2 = cv2.morphologyEx(thresh2, cv2.MORPH_CLOSE, kernel)
    processed_images.append(thresh2)
    
    # 方案3：CLAHE增强 + 双边滤波
    gray3 = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray3 = clahe.apply(gray3)
    gray3 = cv2.bilateralFilter(gray3, 9, 75, 75)
    thresh3 = cv2.adaptiveThreshold(gray3, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 2)
    processed_images.append(thresh3)
    
    # 方案4：边缘检测 + 轮廓填充
    gray4 = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    edges = cv2.Canny(gray4, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    processed_images.append(edges)
    
    return processed_images

def ultra_preprocess_for_letters(img: np.ndarray) -> List[np.ndarray]:
    """为字母识别提供多种预处理方案"""
    processed_images = []
    
    # 转换为灰度图
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # 方案1：超高倍放大 + 多级处理
    gray1 = cv2.resize(gray, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
    gray1 = cv2.GaussianBlur(gray1, (3, 3), 0)
    gray1 = cv2.equalizeHist(gray1)
    thresh1 = cv2.adaptiveThreshold(gray1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh1 = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
    processed_images.append(thresh1)
    
    # 方案2：CLAHE + 双边滤波 + Otsu
    gray2 = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray2 = clahe.apply(gray2)
    gray2 = cv2.bilateralFilter(gray2, 9, 75, 75)
    _, thresh2 = cv2.threshold(gray2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(thresh2)
    
    # 方案3：边缘检测 + 形态学操作
    gray3 = cv2.resize(gray, None, fx=7, fy=7, interpolation=cv2.INTER_CUBIC)
    gray3 = cv2.GaussianBlur(gray3, (3, 3), 0)
    edges = cv2.Canny(gray3, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    processed_images.append(edges)
    
    # 方案4：多尺度处理
    gray4 = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    gray4 = cv2.GaussianBlur(gray4, (5, 5), 0)
    thresh4 = cv2.adaptiveThreshold(gray4, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh4 = cv2.morphologyEx(thresh4, cv2.MORPH_CLOSE, kernel)
    processed_images.append(thresh4)
    
    return processed_images

def multi_engine_recognize(img: np.ndarray, ocr_manager: OCRManager, is_grade: bool = False) -> Tuple[str, float]:
    """多引擎融合识别"""
    results = []
    confidences = []
    
    # 获取所有可用引擎
    engines = list(ocr_manager.engines.keys())
    
    # 为每个引擎尝试多种预处理方案
    if is_grade:
        processed_images = ultra_preprocess_for_letters(img)
    else:
        processed_images = ultra_preprocess_for_numbers(img)
    
    for engine in engines:
        for i, processed_img in enumerate(processed_images):
            try:
                text = ocr_manager.recognize_text(processed_img, engine, is_grade)
                if text.strip():
                    results.append(text.strip())
                    # 简单的置信度估算（基于文本长度和字符类型）
                    confidence = calculate_confidence(text, is_grade)
                    confidences.append(confidence)
                    print(f"DEBUG {engine} 方案{i+1}: '{text}' (置信度: {confidence:.2f})")
            except Exception as e:
                print(f"DEBUG {engine} 方案{i+1} 失败: {e}")
    
    if not results:
        return "", 0.0
    
    # 选择最佳结果
    best_result, best_confidence = select_best_result(results, confidences, is_grade)
    return best_result, best_confidence

def calculate_confidence(text: str, is_grade: bool = False) -> float:
    """计算识别结果的置信度"""
    if not text:
        return 0.0
    
    confidence = 0.5  # 基础置信度
    
    if is_grade:
        # 级别识别的置信度计算
        text_upper = text.upper()
        
        # 检查是否包含有效级别字符
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ-')
        char_ratio = sum(1 for c in text_upper if c in valid_chars) / len(text_upper) if text_upper else 0
        confidence += char_ratio * 0.3
        
        # 检查是否匹配已知级别模式
        if any(grade in text_upper for grade in ['AAA', 'AA', 'A', 'B', 'C']):
            confidence += 0.2
        
        # 长度惩罚（级别应该较短）
        if len(text) <= 5:
            confidence += 0.1
        else:
            confidence -= min(0.2, (len(text) - 5) * 0.05)
    else:
        # 数字识别的置信度计算
        valid_chars = set('0123456789+-.')
        char_ratio = sum(1 for c in text if c in valid_chars) / len(text) if text else 0
        confidence += char_ratio * 0.4
        
        # 检查是否包含数字
        if any(c.isdigit() for c in text):
            confidence += 0.2
        
        # 长度适中（数字通常不会太长）
        if 1 <= len(text) <= 10:
            confidence += 0.1
        else:
            confidence -= min(0.2, abs(len(text) - 5) * 0.05)
    
    return min(1.0, max(0.0, confidence))

def select_best_result(results: List[str], confidences: List[float], is_grade: bool = False) -> Tuple[str, float]:
    """选择最佳识别结果"""
    if not results:
        return "", 0.0
    
    # 找到最高置信度的结果
    max_confidence_idx = confidences.index(max(confidences))
    best_result = results[max_confidence_idx]
    best_confidence = confidences[max_confidence_idx]
    
    # 如果置信度太低，尝试结果融合
    if best_confidence < 0.7:
        fused_result = fuse_results(results, is_grade)
        if fused_result:
            fused_confidence = calculate_confidence(fused_result, is_grade)
            if fused_confidence > best_confidence:
                return fused_result, fused_confidence
    
    return best_result, best_confidence

def fuse_results(results: List[str], is_grade: bool = False) -> str:
    """融合多个识别结果"""
    if not results:
        return ""
    
    if is_grade:
        # 级别融合：选择最常见的有效级别
        valid_grades = []
        for result in results:
            result_upper = result.upper()
            for grade in ['AAA', 'AA', 'A', 'B', 'C']:
                if grade in result_upper:
                    valid_grades.append(grade)
                    break
        
        if valid_grades:
            # 返回最常见的级别
            from collections import Counter
            most_common = Counter(valid_grades).most_common(1)[0][0]
            return most_common
    else:
        # 数字融合：选择最一致的数字
        numbers = []
        for result in results:
            # 提取数字部分
            import re
            nums = re.findall(r'[+-]?\d+\.?\d*', result)
            if nums:
                try:
                    numbers.append(float(nums[0]))
                except ValueError:
                    continue
        
        if numbers:
            # 返回最接近平均值的数字
            avg = sum(numbers) / len(numbers)
            closest = min(numbers, key=lambda x: abs(x - avg))
            return str(closest)
    
    return ""

def parse_power(text: str) -> Tuple[float, float]:
    """解析主力等级，返回值和置信度"""
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
        value = float(num) if num else float("nan")
        confidence = calculate_confidence(text, is_grade=False)
        return value, confidence
    except Exception:
        return float("nan"), 0.0

def normalize_grade(text: str) -> Tuple[str, float]:
    """规范化级别，返回值和置信度"""
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
        return "", 0.0
    
    result = sign + grade
    confidence = calculate_confidence(text, is_grade=True)
    return result, confidence

def grade_rank(grade: str) -> int:
    """级别排序"""
    if not grade:
        return -1
    g = grade[1:] if grade.startswith("-") else grade
    try:
        return GRADES_ORDER.index(g)
    except ValueError:
        return -1

def decide_signal(powers: List[Tuple[float, float]], grades: List[Tuple[str, float]]) -> str:
    """信号判断（考虑置信度）"""
    # 只考虑高置信度的结果
    high_conf_powers = [p[0] for p in powers if not np.isnan(p[0]) and p[1] > 0.6]
    high_conf_grades = [g[0] for g in grades if g[0] and g[1] > 0.6]
    
    pos_cnt = sum(1 for v in high_conf_powers if v > 0)
    neg_cnt = sum(1 for v in high_conf_powers if v < 0)

    high_pos = sum(1 for g in high_conf_grades if g and not g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))
    high_neg = sum(1 for g in high_conf_grades if g.startswith("-") and grade_rank(g) >= GRADES_ORDER.index("A"))

    if pos_cnt >= 6 and high_pos >= 3:  # 降低阈值，因为只考虑高置信度结果
        return "做多"
    if neg_cnt >= 6 and high_neg >= 3:
        return "做空"
    return "观望"

def process_panel_precision(img: np.ndarray, name: str, rois: Dict, ocr_manager: OCRManager) -> Tuple[float, float, str, float]:
    """高精度处理单个板块"""
    try:
        x1, y1, w1, h1 = rois[name]["power"]
        x2, y2, w2, h2 = rois[name]["grade"]

        crop_power = img[y1:y1+h1, x1:x1+w1]
        crop_grade = img[y2:y2+h2, x2:x2+w2]

        # 多引擎融合识别
        txt_power, power_conf = multi_engine_recognize(crop_power, ocr_manager, is_grade=False)
        txt_grade, grade_conf = multi_engine_recognize(crop_grade, ocr_manager, is_grade=True)

        # 解析结果
        val_power, parse_power_conf = parse_power(txt_power)
        val_grade, parse_grade_conf = normalize_grade(txt_grade)
        
        # 综合置信度
        final_power_conf = (power_conf + parse_power_conf) / 2
        final_grade_conf = (grade_conf + parse_grade_conf) / 2
        
        print(f"DEBUG {name}: 主力等级='{txt_power}'->{val_power} (置信度:{final_power_conf:.2f})")
        print(f"DEBUG {name}: 级别='{txt_grade}'->'{val_grade}' (置信度:{final_grade_conf:.2f})")

        return val_power, final_power_conf, val_grade, final_grade_conf
    except Exception as e:
        print(f"处理板块 {name} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return float("nan"), 0.0, "", 0.0

def load_rois(path: str) -> Dict[str, Dict[str, Tuple[int, int, int, int]]]:
    """加载ROI配置"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_debug_images(img: np.ndarray, rois: Dict, cycle_count: int) -> None:
    """保存调试图像"""
    debug_dir = "../data/precision_debug"
    os.makedirs(debug_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存完整截图
    cv2.imwrite(f"{debug_dir}/fullscreen_{timestamp}_cycle{cycle_count}.png", img)
    
    # 保存每个板块的裁剪图像
    for name in PANEL_NAMES:
        x1, y1, w1, h1 = rois[name]["power"]
        x2, y2, w2, h2 = rois[name]["grade"]
        
        crop_power = img[y1:y1+h1, x1:x1+w1]
        crop_grade = img[y2:y2+h2, x2:x2+w2]
        
        cv2.imwrite(f"{debug_dir}/{name}_power_{timestamp}_cycle{cycle_count}.png", crop_power)
        cv2.imwrite(f"{debug_dir}/{name}_grade_{timestamp}_cycle{cycle_count}.png", crop_grade)

def main():
    """主函数 - 高精度版本"""
    print("=== 高精度监控系统启动 ===")
    print("专注于最高识别精度，不考虑处理时间")
    
    # 初始化
    rois = load_rois("../data/rois.json")
    ocr_manager = OCRManager()
    
    if not ocr_manager.engines:
        print("❌ 没有可用的OCR引擎，请先安装")
        return
    
    print(f"✓ 可用OCR引擎: {list(ocr_manager.engines.keys())}")
    print("✓ 使用多引擎融合识别")
    print("✓ 启用高级图像预处理")
    print("✓ 启用置信度评分机制")
    
    out_csv = f"../data/ticks_precision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 创建截图保存目录
    screenshot_dir = "../data/precision_screenshots"
    debug_dir = "../data/precision_debug"
    os.makedirs(screenshot_dir, exist_ok=True)
    os.makedirs(debug_dir, exist_ok=True)
    
    print(f"✓ 监控 {len(rois)} 个板块")
    print(f"✓ 输出文件: {out_csv}")
    print(f"✓ 截图目录: {screenshot_dir}")
    print(f"✓ 调试目录: {debug_dir}")
    print("\n=== 开始高精度监控循环 ===")

    header = ["timestamp"]
    for name in PANEL_NAMES:
        header += [f"{name}_主力等级", f"{name}_主力等级置信度", f"{name}_级别", f"{name}_级别置信度"]
    header += ["结论", "截图文件", "平均置信度"]

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(header)
        fcsv.flush()

        with mss() as sct:
            cycle_count = 0
            
            while True:
                cycle_start = time.time()
                cycle_count += 1
                
                print(f"\n--- 第 {cycle_count} 次循环开始 ---")
                
                # 截图
                img = grab_fullscreen(sct)
                
                # 保存完整页面截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = f"{screenshot_dir}/fullscreen_{timestamp}.png"
                cv2.imwrite(screenshot_filename, img)
                
                # 保存调试图像（每10次循环保存一次）
                if cycle_count % 10 == 0:
                    save_debug_images(img, rois, cycle_count)
                
                # 记录当前时间戳
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 串行处理所有板块（确保每个板块都得到充分处理）
                powers = []
                power_confs = []
                grades = []
                grade_confs = []
                
                for name in PANEL_NAMES:
                    print(f"处理板块: {name}")
                    power, power_conf, grade, grade_conf = process_panel_precision(img, name, rois, ocr_manager)
                    powers.append(power)
                    power_confs.append(power_conf)
                    grades.append(grade)
                    grade_confs.append(grade_conf)
                
                # 信号判断
                power_data = list(zip(powers, power_confs))
                grade_data = list(zip(grades, grade_confs))
                signal = decide_signal(power_data, grade_data)
                
                # 计算平均置信度
                all_confs = power_confs + grade_confs
                avg_confidence = sum(all_confs) / len(all_confs) if all_confs else 0.0
                
                # 写入CSV
                row = [current_time]
                for i in range(8):
                    row.append(powers[i])
                    row.append(power_confs[i])
                    row.append(grades[i])
                    row.append(grade_confs[i])
                row.append(signal)
                row.append(screenshot_filename)
                row.append(avg_confidence)
                
                with lock:
                    writer.writerow(row)
                    fcsv.flush()
                
                # 时间统计
                cycle_elapsed = time.time() - cycle_start
                
                print(f"第 {cycle_count} 次循环完成:")
                print(f"  耗时: {cycle_elapsed:.2f}秒")
                print(f"  信号: {signal}")
                print(f"  平均置信度: {avg_confidence:.2f}")
                print(f"  主力等级置信度: {[f'{c:.2f}' for c in power_confs]}")
                print(f"  级别置信度: {[f'{c:.2f}' for c in grade_confs]}")
                
                # 高置信度结果统计
                high_conf_count = sum(1 for c in all_confs if c > 0.7)
                print(f"  高置信度结果: {high_conf_count}/{len(all_confs)}")
                
                # 等待下一轮（高精度模式不限制时间）
                time.sleep(2.0)  # 固定间隔，确保充分处理

if __name__ == "__main__":
    main()
