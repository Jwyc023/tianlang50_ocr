# -*- coding: utf-8 -*-
"""
单张截图识别使用示例
演示如何使用recognize_single_image.py识别指定的截图
"""

import os
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入recognize_single_image模块
try:
    from recognize_single_image import recognize_single_image
except ImportError:
    # 如果导入失败，尝试从当前目录导入
    sys.path.append(os.path.dirname(__file__))
    from recognize_single_image import recognize_single_image


def example_recognize_existing_screenshot():
    """识别现有截图的示例"""
    print("=== 识别现有截图示例 ===")
    
    # 查找现有的截图文件
    screenshots_dir = "../data/fast_screenshots"
    if not os.path.exists(screenshots_dir):
        print(f"❌ 截图目录不存在: {screenshots_dir}")
        return
    
    # 获取最新的截图文件
    screenshot_files = list(Path(screenshots_dir).glob("*.png"))
    if not screenshot_files:
        print(f"❌ 截图目录中没有PNG文件: {screenshots_dir}")
        return
    
    # 选择最新的截图
    latest_screenshot = max(screenshot_files, key=lambda x: x.stat().st_mtime)
    print(f"选择最新截图: {latest_screenshot.name}")
    
    # ROI配置文件路径
    roi_config_path = "../data/rois.json"
    
    # 识别截图
    results = recognize_single_image(
        str(latest_screenshot),
        roi_config_path if os.path.exists(roi_config_path) else None,
        save_debug=True
    )
    
    if "error" in results:
        print(f"❌ 识别失败: {results['error']}")
        return
    
    # 显示结果
    print(f"\n=== 识别结果 ===")
    print(f"图片: {results['image_path']}")
    print(f"尺寸: {results['image_size']}")
    print(f"OCR引擎: {', '.join(results['ocr_engines'])}")
    
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


def example_recognize_custom_image():
    """识别自定义图片的示例"""
    print("=== 识别自定义图片示例 ===")
    
    # 让用户输入图片路径
    image_path = input("请输入图片文件路径: ").strip()
    
    if not image_path:
        print("❌ 未输入图片路径")
        return
    
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        return
    
    # 询问是否使用ROI配置
    roi_config_path = "../data/rois.json"
    use_roi = input(f"是否使用ROI配置? (y/n) [默认: y]: ").strip().lower()
    
    if use_roi in ['', 'y', 'yes'] and os.path.exists(roi_config_path):
        roi_path = roi_config_path
        print(f"使用ROI配置: {roi_path}")
    else:
        roi_path = None
        print("不使用ROI配置，将识别整个图片")
    
    # 识别图片
    results = recognize_single_image(image_path, roi_path, save_debug=True)
    
    if "error" in results:
        print(f"❌ 识别失败: {results['error']}")
        return
    
    # 显示结果
    print(f"\n=== 识别结果 ===")
    print(f"图片: {results['image_path']}")
    print(f"尺寸: {results['image_size']}")
    print(f"OCR引擎: {', '.join(results['ocr_engines'])}")
    
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


def example_batch_recognize():
    """批量识别示例"""
    print("=== 批量识别示例 ===")
    
    # 查找截图目录
    screenshots_dir = "../data/fast_screenshots"
    if not os.path.exists(screenshots_dir):
        print(f"❌ 截图目录不存在: {screenshots_dir}")
        return
    
    # 获取所有截图文件
    screenshot_files = list(Path(screenshots_dir).glob("*.png"))
    if not screenshot_files:
        print(f"❌ 截图目录中没有PNG文件: {screenshots_dir}")
        return
    
    # 限制处理数量（避免处理太多）
    max_files = 5
    files_to_process = screenshot_files[:max_files]
    
    print(f"将处理 {len(files_to_process)} 个截图文件")
    
    # ROI配置文件路径
    roi_config_path = "../data/rois.json"
    
    # 批量识别
    all_results = []
    for i, screenshot_file in enumerate(files_to_process):
        print(f"\n--- 处理第 {i+1}/{len(files_to_process)} 个文件: {screenshot_file.name} ---")
        
        results = recognize_single_image(
            str(screenshot_file),
            roi_config_path if os.path.exists(roi_config_path) else None,
            save_debug=False  # 批量处理时不保存调试图片
        )
        
        if "error" not in results:
            all_results.append(results)
            print(f"✓ 识别完成")
        else:
            print(f"❌ 识别失败: {results['error']}")
    
    # 显示批量结果总结
    print(f"\n=== 批量识别总结 ===")
    print(f"成功识别: {len(all_results)}/{len(files_to_process)}")
    
    if all_results:
        print(f"\n各文件识别结果:")
        for i, results in enumerate(all_results):
            print(f"\n文件 {i+1}: {Path(results['image_path']).name}")
            
            if results["roi_results"]:
                for name, data in results["roi_results"].items():
                    if "error" not in data:
                        power_val = data["power"]["parsed_value"]
                        grade_val = data["grade"]["parsed_value"]
                        print(f"  {name}: 主力等级={power_val}, 级别='{grade_val}'")


def main():
    """主函数"""
    print("单张截图识别程序使用示例")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 识别现有截图（最新的一张）")
        print("2. 识别自定义图片")
        print("3. 批量识别截图")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            example_recognize_existing_screenshot()
        elif choice == "2":
            example_recognize_custom_image()
        elif choice == "3":
            example_batch_recognize()
        elif choice == "4":
            print("退出程序")
            break
        else:
            print("❌ 无效选择，请重新输入")
        
        print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
