# -*- coding: utf-8 -*-
"""
OCR替代方案安装脚本
自动安装PaddleOCR和EasyOCR
"""

import subprocess
import sys
import os

def install_package(package_name):
    """安装Python包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✓ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def main():
    """主安装函数"""
    print("=== OCR替代方案安装脚本 ===")
    print("本脚本将安装PaddleOCR和EasyOCR作为Tesseract的替代方案")
    print()
    
    # 检查当前目录
    if not os.path.exists("src"):
        print("❌ 请在项目根目录运行此脚本")
        return
    
    # 安装PaddleOCR
    print("1. 安装PaddleOCR...")
    paddle_success = install_package("paddlepaddle")
    if paddle_success:
        install_package("paddleocr")
    
    print()
    
    # 安装EasyOCR
    print("2. 安装EasyOCR...")
    easy_success = install_package("easyocr")
    
    print()
    
    # 安装其他依赖
    print("3. 安装其他依赖...")
    install_package("opencv-python")
    install_package("numpy")
    install_package("pillow")
    
    print()
    print("=== 安装完成 ===")
    
    if paddle_success:
        print("✓ PaddleOCR 已安装，可以用于高精度文字识别")
    
    if easy_success:
        print("✓ EasyOCR 已安装，可以用于多语言文字识别")
    
    print()
    print("使用方法:")
    print("1. 运行 python src/ocr_alternatives.py 测试所有引擎")
    print("2. 在 monitor_fast.py 中集成新的OCR引擎")
    print("3. 使用对比测试功能选择最佳引擎")

if __name__ == "__main__":
    main()
