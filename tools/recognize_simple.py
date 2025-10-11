# -*- coding: utf-8 -*-
"""
简化版单张截图识别程序
只使用Tesseract OCR，避免PaddleOCR兼容性问题
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("❌ pytesseract 未安装，请先安装: pip install pytesseract")


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


def tesseract_recognize(img: np.ndarray, is_grade: bool = False) -> str:
    """使用Tesseract进行识别"""
    if not TESSERACT_AVAILABLE:
        return ""
    
    if is_grade:
        # 级别识别：单字符模式，纯英文
        cfg = "--psm 10 -l eng --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ-"
    else:
        # 主力等级：数字识别
        cfg = "--psm 7 -l eng --oem 3 -c tessedit_char_whitelist=0123456789+-."
    
    try:
        text = pytesseract.image_to_string(img, config=cfg)
        return text.strip()
    except Exception as e:
        print(f"Tesseract识别失败: {e}")
        return ""


def multi_preprocess_recognize(img: np.ndarray, is_grade: bool = False) -> Tuple[str, float]:
    """多预处理方案识别"""
    if not TESSERACT_AVAILABLE:
        return "", 0.0
    
    results = []
    confidences = []
    
    # 获取预处理方案
    if is_grade:
        processed_images = ultra_preprocess_for_letters(img)
    else:
        processed_images = ultra_preprocess_for_numbers(img)
    
    print(f"使用 {len(processed_images)} 种预处理方案")
    
    # 对每种预处理方案进行识别
    for i, processed_img in enumerate(processed_images):
        try:
            text = tesseract_recognize(processed_img, is_grade)
            if text.strip():
                results.append(text.strip())
                # 简单的置信度估算
                confidence = calculate_confidence(text, is_grade)
                confidences.append(confidence)
                print(f"  方案{i+1}: '{text}' (置信度: {confidence:.2f})")
        except Exception as e:
            print(f"  方案{i+1} 失败: {e}")
    
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
    
    return best_result, best_confidence


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


def load_rois(path: str) -> Dict[str, Dict[str, List[int]]]:
    """加载ROI配置"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def recognize_single_image_simple(image_path: str, roi_config_path: str = None, save_debug: bool = True) -> Dict:
    """
    简化版单张截图识别（只使用Tesseract）
    
    Args:
        image_path: 截图文件路径
        roi_config_path: ROI配置文件路径（可选）
        save_debug: 是否保存调试图片
    
    Returns:
        识别结果字典
    """
    print(f"=== 识别截图: {image_path} ===")
    
    if not TESSERACT_AVAILABLE:
        return {"error": "Tesseract OCR 不可用，请先安装 pytesseract"}
    
    # 检查图片文件是否存在
    if not os.path.exists(image_path):
        return {"error": f"图片文件不存在: {image_path}"}
    
    # 加载图片
    img = cv2.imread(image_path)
    if img is None:
        return {"error": "无法加载图片文件"}
    
    print(f"图片尺寸: {img.shape}")
    
    # 加载ROI配置（如果提供）
    rois = None
    if roi_config_path and os.path.exists(roi_config_path):
        try:
            rois = load_rois(roi_config_path)
            print(f"已加载ROI配置: {len(rois)} 个板块")
        except Exception as e:
            print(f"⚠️ ROI配置加载失败: {e}")
            rois = None
    
    # 创建调试目录
    debug_dir = "debug_images"
    if save_debug:
        os.makedirs(debug_dir, exist_ok=True)
    
    results = {
        "image_path": image_path,
        "image_size": img.shape,
        "ocr_engine": "tesseract",
        "roi_results": {},
        "full_image_results": {}
    }
    
    # 如果有ROI配置，识别各个板块
    if rois:
        print(f"\n=== 识别ROI区域 ===")
        for name, roi_data in rois.items():
            print(f"\n处理板块: {name}")
            
            try:
                # 提取ROI区域
                x1, y1, w1, h1 = roi_data["power"]
                x2, y2, w2, h2 = roi_data["grade"]
                
                crop_power = img[y1:y1+h1, x1:x1+w1]
                crop_grade = img[y2:y2+h2, x2:x2+w2]
                
                # 保存ROI图片（用于调试）
                if save_debug:
                    cv2.imwrite(f"{debug_dir}/{name}_power.png", crop_power)
                    cv2.imwrite(f"{debug_dir}/{name}_grade.png", crop_grade)
                
                print(f"  主力等级区域: {x1},{y1},{w1},{h1}")
                print(f"  级别区域: {x2},{y2},{w2},{h2}")
                
                # 多预处理方案识别
                print("  识别主力等级:")
                txt_power, power_conf = multi_preprocess_recognize(crop_power, is_grade=False)
                val_power, parse_power_conf = parse_power(txt_power)
                final_power_conf = (power_conf + parse_power_conf) / 2
                
                print("  识别级别:")
                txt_grade, grade_conf = multi_preprocess_recognize(crop_grade, is_grade=True)
                val_grade, parse_grade_conf = normalize_grade(txt_grade)
                final_grade_conf = (grade_conf + parse_grade_conf) / 2
                
                results["roi_results"][name] = {
                    "power": {
                        "raw_text": txt_power,
                        "parsed_value": val_power,
                        "confidence": final_power_conf
                    },
                    "grade": {
                        "raw_text": txt_grade,
                        "parsed_value": val_grade,
                        "confidence": final_grade_conf
                    }
                }
                
                print(f"  结果: 主力等级={val_power} (置信度:{final_power_conf:.2f}), 级别='{val_grade}' (置信度:{final_grade_conf:.2f})")
                
            except Exception as e:
                print(f"  处理板块 {name} 时出错: {e}")
                results["roi_results"][name] = {"error": str(e)}
    
    # 识别整个图片
    print(f"\n=== 识别整个图片 ===")
    
    # 数字识别
    print("识别数字内容:")
    txt_numbers, numbers_conf = multi_preprocess_recognize(img, is_grade=False)
    
    # 字母识别
    print("识别字母内容:")
    txt_letters, letters_conf = multi_preprocess_recognize(img, is_grade=True)
    
    results["full_image_results"] = {
        "numbers": {
            "text": txt_numbers,
            "confidence": numbers_conf
        },
        "letters": {
            "text": txt_letters,
            "confidence": letters_conf
        }
    }
    
    print(f"整个图片识别结果:")
    print(f"  数字: '{txt_numbers}' (置信度: {numbers_conf:.2f})")
    print(f"  字母: '{txt_letters}' (置信度: {letters_conf:.2f})")
    
    # 保存调试图片
    if save_debug:
        cv2.imwrite(f"{debug_dir}/original.png", img)
        print(f"\n✓ 调试图片已保存到: {debug_dir}/")
    
    return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="简化版单张截图识别程序（只使用Tesseract）")
    parser.add_argument("image_path", help="截图文件路径")
    parser.add_argument("-r", "--roi", help="ROI配置文件路径")
    parser.add_argument("--no-debug", action="store_true", help="不保存调试图片")
    
    args = parser.parse_args()
    
    # 识别截图
    results = recognize_single_image_simple(
        args.image_path, 
        args.roi, 
        save_debug=not args.no_debug
    )
    
    if "error" in results:
        print(f"❌ 识别失败: {results['error']}")
        return 1
    
    # 显示总结
    print(f"\n=== 识别总结 ===")
    print(f"图片: {results['image_path']}")
    print(f"尺寸: {results['image_size']}")
    print(f"OCR引擎: {results['ocr_engine']}")
    
    if results["roi_results"]:
        print(f"\nROI区域识别结果:")
        for name, data in results["roi_results"].items():
            if "error" in data:
                print(f"  {name}: 错误 - {data['error']}")
            else:
                power_val = data["power"]["parsed_value"]
                power_conf = data["power"]["confidence"]
                grade_val = data["grade"]["parsed_value"]
                grade_conf = data["grade"]["confidence"]
                print(f"  {name}: 主力等级={power_val} ({power_conf:.2f}), 级别='{grade_val}' ({grade_conf:.2f})")
    
    if results["full_image_results"]:
        print(f"\n整个图片识别结果:")
        numbers = results["full_image_results"]["numbers"]
        letters = results["full_image_results"]["letters"]
        print(f"  数字: '{numbers['text']}' (置信度: {numbers['confidence']:.2f})")
        print(f"  字母: '{letters['text']}' (置信度: {letters['confidence']:.2f})")
    
    return 0


if __name__ == "__main__":
    exit(main())

