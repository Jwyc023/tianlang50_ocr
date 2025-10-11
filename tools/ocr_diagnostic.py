# -*- coding: utf-8 -*-
"""
OCR测试诊断程序
用于诊断OCR引擎初始化问题
"""

import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_ocr_engines():
    """测试各个OCR引擎的初始化"""
    print("=== OCR引擎诊断测试 ===")
    
    # 测试Tesseract
    print("\n1. 测试Tesseract OCR...")
    try:
        import pytesseract
        print("✓ pytesseract 导入成功")
        
        # 测试Tesseract路径
        try:
            pytesseract.get_tesseract_version()
            print("✓ Tesseract 可执行文件正常")
        except Exception as e:
            print(f"❌ Tesseract 可执行文件问题: {e}")
            
    except ImportError as e:
        print(f"❌ pytesseract 导入失败: {e}")
    
    # 测试PaddleOCR
    print("\n2. 测试PaddleOCR...")
    try:
        from paddleocr import PaddleOCR
        print("✓ paddleocr 导入成功")
        
        # 测试PaddleOCR初始化
        try:
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            print("✓ PaddleOCR 初始化成功")
        except Exception as e:
            print(f"❌ PaddleOCR 初始化失败: {e}")
            
    except ImportError as e:
        print(f"❌ paddleocr 导入失败: {e}")
    
    # 测试EasyOCR
    print("\n3. 测试EasyOCR...")
    try:
        import easyocr
        print("✓ easyocr 导入成功")
        
        # 测试EasyOCR初始化
        try:
            reader = easyocr.Reader(['en'])
            print("✓ EasyOCR 初始化成功")
        except Exception as e:
            print(f"❌ EasyOCR 初始化失败: {e}")
            
    except ImportError as e:
        print(f"❌ easyocr 导入失败: {e}")
    
    # 测试OCR管理器
    print("\n4. 测试OCR管理器...")
    try:
        from ocr_alternatives import OCRManager
        print("✓ OCRManager 导入成功")
        
        # 测试OCR管理器初始化
        try:
            ocr_manager = OCRManager()
            print(f"✓ OCRManager 初始化成功，可用引擎: {list(ocr_manager.engines.keys())}")
        except Exception as e:
            print(f"❌ OCRManager 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"❌ OCRManager 导入失败: {e}")
        import traceback
        traceback.print_exc()

def test_simple_recognition():
    """测试简单识别功能"""
    print("\n=== 简单识别测试 ===")
    
    try:
        from ocr_alternatives import OCRManager
        import cv2
        import numpy as np
        
        # 创建一个简单的测试图像
        test_img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, "TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        print("✓ 测试图像创建成功")
        
        # 初始化OCR管理器
        ocr_manager = OCRManager()
        
        if not ocr_manager.engines:
            print("❌ 没有可用的OCR引擎")
            return
        
        print(f"可用引擎: {list(ocr_manager.engines.keys())}")
        
        # 测试识别
        for engine_name in ocr_manager.engines.keys():
            try:
                print(f"\n测试 {engine_name}...")
                result = ocr_manager.recognize_text(test_img, engine_name, is_grade=False)
                print(f"✓ {engine_name} 识别结果: '{result}'")
            except Exception as e:
                print(f"❌ {engine_name} 识别失败: {e}")
        
    except Exception as e:
        print(f"❌ 简单识别测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_engines()
    test_simple_recognition()
    
    print("\n=== 诊断完成 ===")
    print("如果所有测试都通过，说明OCR引擎工作正常")
    print("如果有失败的测试，请根据错误信息进行修复")

