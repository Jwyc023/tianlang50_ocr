# -*- coding: utf-8 -*-
"""
时间轴监控 - 完整工作流程演示
帮助用户快速上手
"""

import os
import sys

def print_step(step, title):
    """打印步骤标题"""
    print(f"\n{'='*60}")
    print(f"步骤 {step}: {title}")
    print('='*60)

def check_dependencies():
    """检查依赖项"""
    print_step(0, "检查依赖项")
    
    missing = []
    
    try:
        import cv2
        print("✓ opencv-python")
    except ImportError:
        missing.append("opencv-python")
        print("✗ opencv-python")
    
    try:
        import numpy
        print("✓ numpy")
    except ImportError:
        missing.append("numpy")
        print("✗ numpy")
    
    try:
        import pytesseract
        print("✓ pytesseract")
    except ImportError:
        missing.append("pytesseract")
        print("✗ pytesseract")
    
    try:
        import pyautogui
        print("✓ pyautogui")
    except ImportError:
        missing.append("pyautogui")
        print("✗ pyautogui")
    
    try:
        import mss
        print("✓ mss")
    except ImportError:
        missing.append("mss")
        print("✗ mss")
    
    if missing:
        print(f"\n缺少以下依赖项: {', '.join(missing)}")
        print("请运行以下命令安装:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n✓ 所有依赖项已安装")
    return True

def check_rois():
    """检查ROI配置"""
    print_step(1, "检查ROI配置")
    
    rois_path = "../data/rois.json"
    if os.path.exists(rois_path):
        print(f"✓ ROI配置文件已存在: {rois_path}")
        return True
    else:
        print(f"✗ ROI配置文件不存在: {rois_path}")
        print("请先运行ROI校准工具:")
        print("  cd tools")
        print("  python calibrate_rois.py")
        return False

def calibrate_timeline():
    """校准时间轴"""
    print_step(2, "校准时间轴")
    
    config_path = "../data/timeline_config.json"
    if os.path.exists(config_path):
        print(f"✓ 时间轴配置已存在: {config_path}")
        print("如需重新校准，请运行:")
        print("  python calibrate_timeline.py")
        recalibrate = input("\n是否重新校准？(y/n): ").strip().lower()
        if recalibrate == 'y':
            os.system("python calibrate_timeline.py")
        return True
    else:
        print(f"✗ 时间轴配置不存在: {config_path}")
        print("即将启动校准工具...")
        input("按 Enter 继续...")
        os.system("python calibrate_timeline.py")
        
        if os.path.exists(config_path):
            print("\n✓ 校准完成")
            return True
        else:
            print("\n✗ 校准未完成")
            return False

def test_run():
    """测试运行"""
    print_step(3, "测试运行")
    
    print("建议先进行测试运行，只采集5个时间点")
    print("这将验证:")
    print("  - 鼠标移动位置是否准确")
    print("  - OCR识别是否正常")
    print("  - 数据记录是否正确")
    
    test = input("\n是否进行测试运行？(y/n): ").strip().lower()
    if test == 'y':
        print("\n准备测试运行...")
        print("请确保:")
        print("  1. 时间轴界面已打开")
        print("  2. 时间轴完整可见（9:30到15:00）")
        print("  3. 8个板块的显示区域可见")
        input("\n准备好后按 Enter 开始...")
        
        os.chdir("../src")
        os.system("python monitor_timeline.py --test")
        os.chdir("../tools")
        
        print("\n测试完成!")
        print("请检查输出的CSV文件，确认数据准确性")
        
        csv_dir = "../data"
        print(f"CSV文件位置: {csv_dir}")
        
        correct = input("\n数据是否正确？(y/n): ").strip().lower()
        return correct == 'y'
    else:
        return True

def full_run():
    """完整运行"""
    print_step(4, "完整运行")
    
    print("准备进行完整数据采集")
    print("注意事项:")
    print("  - 采集约330个时间点，耗时10-15分钟")
    print("  - 期间不要操作电脑")
    print("  - 保持界面稳定，不要遮挡")
    print("  - 可以移动鼠标到左上角中断")
    
    run = input("\n是否开始完整运行？(y/n): ").strip().lower()
    if run == 'y':
        print("\n准备完整运行...")
        input("按 Enter 开始...")
        
        os.chdir("../src")
        os.system("python monitor_timeline.py")
        os.chdir("../tools")
        
        print("\n✓ 完整采集完成!")
        print("数据已保存到 data/ 目录")

def main():
    """主流程"""
    print("="*60)
    print("时间轴监控 - 完整工作流程向导")
    print("="*60)
    print("\n本向导将引导你完成:")
    print("  1. 检查依赖项")
    print("  2. 检查ROI配置")
    print("  3. 校准时间轴")
    print("  4. 测试运行")
    print("  5. 完整运行")
    
    input("\n按 Enter 开始...")
    
    # 步骤0: 检查依赖
    if not check_dependencies():
        print("\n请先安装依赖项后再运行本程序")
        return
    
    # 步骤1: 检查ROI
    if not check_rois():
        print("\n请先完成ROI校准后再运行本程序")
        return
    
    # 步骤2: 校准时间轴
    if not calibrate_timeline():
        print("\n时间轴校准失败")
        return
    
    # 步骤3: 测试运行
    if not test_run():
        print("\n测试未通过，请检查配置")
        return
    
    # 步骤4: 完整运行
    full_run()
    
    print("\n"+ "="*60)
    print("工作流程完成!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


