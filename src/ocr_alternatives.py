# -*- coding: utf-8 -*-
"""
OCR替代方案模块
提供多种OCR引擎的对比测试
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict
import time

# 尝试导入不同的OCR库
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class OCRManager:
    """OCR管理器，支持多种OCR引擎"""
    
    def __init__(self):
        self.engines = {}
        self._init_engines()
    
    def _init_engines(self):
        """初始化可用的OCR引擎"""
        if TESSERACT_AVAILABLE:
            self.engines['tesseract'] = TesseractOCR()
            print("✓ Tesseract OCR 已加载")
        
        if PADDLEOCR_AVAILABLE:
            self.engines['paddleocr'] = PaddleOCRWrapper()
            print("✓ PaddleOCR 已加载")
        
        if EASYOCR_AVAILABLE:
            self.engines['easyocr'] = EasyOCRWrapper()
            print("✓ EasyOCR 已加载")
        
        if not self.engines:
            print("❌ 没有可用的OCR引擎")
    
    def recognize_text(self, img: np.ndarray, engine: str = 'tesseract', is_grade: bool = False) -> str:
        """使用指定引擎识别文本"""
        if engine not in self.engines:
            raise ValueError(f"OCR引擎 '{engine}' 不可用")
        
        return self.engines[engine].recognize(img, is_grade)
    
    def compare_engines(self, img: np.ndarray, is_grade: bool = False) -> Dict[str, Tuple[str, float]]:
        """对比所有可用引擎的识别结果"""
        results = {}
        
        for name, engine in self.engines.items():
            try:
                start_time = time.time()
                text = engine.recognize(img, is_grade)
                elapsed = time.time() - start_time
                results[name] = (text, elapsed)
            except Exception as e:
                results[name] = (f"错误: {str(e)}", 0.0)
        
        return results


class TesseractOCR:
    """Tesseract OCR包装器"""
    
    def __init__(self):
        self.name = "Tesseract"
    
    def recognize(self, img: np.ndarray, is_grade: bool = False) -> str:
        """Tesseract识别"""
        if is_grade:
            # 级别识别：单字符模式，纯英文
            cfg = "--psm 10 -l eng --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ-"
        else:
            # 主力等级：数字识别
            cfg = "--psm 7 -l eng --oem 3 -c tessedit_char_whitelist=0123456789+-."
        
        text = pytesseract.image_to_string(img, config=cfg)
        return text.strip()


class PaddleOCRWrapper:
    """PaddleOCR包装器"""
    
    def __init__(self):
        self.name = "PaddleOCR"
        # 初始化PaddleOCR，使用轻量级模型
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    
    def recognize(self, img: np.ndarray, is_grade: bool = False) -> str:
        """PaddleOCR识别"""
        try:
            result = self.ocr.ocr(img, cls=True)
            
            if result and result[0]:
                # 提取所有识别到的文本
                texts = []
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]  # 提取文本内容
                        confidence = line[1][1]  # 提取置信度
                        
                        # 只保留高置信度的结果
                        if confidence > 0.5:
                            texts.append(text)
                
                return ' '.join(texts).strip()
            else:
                return ""
        except Exception as e:
            return f"PaddleOCR错误: {str(e)}"


class EasyOCRWrapper:
    """EasyOCR包装器"""
    
    def __init__(self):
        self.name = "EasyOCR"
        # 初始化EasyOCR，只使用英文
        self.reader = easyocr.Reader(['en'])
    
    def recognize(self, img: np.ndarray, is_grade: bool = False) -> str:
        """EasyOCR识别"""
        try:
            results = self.reader.readtext(img)
            
            texts = []
            for (bbox, text, confidence) in results:
                # 只保留高置信度的结果
                if confidence > 0.5:
                    texts.append(text)
            
            return ' '.join(texts).strip()
        except Exception as e:
            return f"EasyOCR错误: {str(e)}"


def enhanced_preprocess_for_letters(img: np.ndarray) -> np.ndarray:
    """专门为字母识别优化的图像预处理"""
    # 1. 转换为灰度图
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # 2. 大幅放大图像（字母识别需要高分辨率）
    scale_factor = 6
    gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    
    # 3. 高斯模糊去噪
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 4. 直方图均衡化增强对比度
    gray = cv2.equalizeHist(gray)
    
    # 5. 形态学操作增强字符
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    
    # 6. 多种阈值方法结合
    # 自适应阈值
    thresh1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Otsu阈值
    _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 结合两种方法
    combined = cv2.bitwise_and(thresh1, thresh2)
    
    # 7. 最终清理
    kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    final = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel_clean)
    
    return final


def test_ocr_engines(img: np.ndarray, is_grade: bool = False) -> None:
    """测试所有OCR引擎的性能"""
    print(f"\n=== OCR引擎对比测试 ({'级别识别' if is_grade else '数字识别'}) ===")
    
    # 预处理图像
    if is_grade:
        processed_img = enhanced_preprocess_for_letters(img)
    else:
        processed_img = img
    
    # 初始化OCR管理器
    ocr_manager = OCRManager()
    
    if not ocr_manager.engines:
        print("❌ 没有可用的OCR引擎")
        return
    
    # 对比测试
    results = ocr_manager.compare_engines(processed_img, is_grade)
    
    print(f"\n识别结果对比:")
    print("-" * 60)
    for engine_name, (text, elapsed) in results.items():
        print(f"{engine_name:12} | 结果: '{text}' | 耗时: {elapsed:.3f}秒")
    print("-" * 60)
    
    # 保存预处理后的图像用于调试
    debug_path = f"../data/debug_preprocessed_{'grade' if is_grade else 'number'}.png"
    cv2.imwrite(debug_path, processed_img)
    print(f"✓ 预处理图像已保存: {debug_path}")


if __name__ == "__main__":
    # 测试代码
    print("OCR替代方案模块已加载")
    print("可用引擎:")
    
    if TESSERACT_AVAILABLE:
        print("  - Tesseract OCR")
    if PADDLEOCR_AVAILABLE:
        print("  - PaddleOCR")
    if EASYOCR_AVAILABLE:
        print("  - EasyOCR")
