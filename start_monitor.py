#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 提供简单的菜单选择
"""

import os
import sys
import subprocess

def print_menu():
    """打印主菜单"""
    print("=" * 50)
    print("天狼50多股同列监控系统")
    print("=" * 50)
    print("1. 校准ROI区域 (首次使用)")
    print("2. 测试OCR识别效果")
    print("3. 开始标准监控")
    print("4. 开始高性能监控")
    print("5. 开始带日志监控 (诊断null数据)")
    print("6. 快速数据分析")
    print("7. 详细数据分析")
    print("8. 日志分析 (分析null数据原因)")
    print("9. 查看失败截图")
    print("10. 调试ROI区域")
    print("11. 环境检查")
    print("0. 退出")
    print("=" * 50)

def run_command(cmd):
    """运行命令"""
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")

def main():
    """主函数"""
    while True:
        print_menu()
        choice = input("请选择操作 (0-11): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            print("🔧 启动ROI校准工具...")
            run_command("python tools/calibrate_rois.py")
        elif choice == "2":
            print("🧪 启动OCR测试工具...")
            run_command("python tools/test_ocr.py")
        elif choice == "3":
            print("📊 启动标准监控...")
            run_command("python src/monitor.py")
        elif choice == "4":
            print("⚡ 启动高性能监控...")
            run_command("python src/monitor_fast.py")
        elif choice == "5":
            print("📝 启动带日志监控 (诊断null数据)...")
            run_command("python src/monitor_with_logging.py")
        elif choice == "6":
            print("📈 启动快速数据分析...")
            run_command("python analysis/quick_analyze.py")
        elif choice == "7":
            print("📊 启动详细数据分析...")
            run_command("python analysis/analyze_csv.py")
        elif choice == "8":
            print("📋 启动日志分析 (分析null数据原因)...")
            run_command("python analysis/log_analyzer.py")
        elif choice == "9":
            print("🖼️ 启动截图查看工具...")
            run_command("python tools/screenshot_viewer.py")
        elif choice == "10":
            print("🔍 启动ROI调试工具...")
            run_command("python tools/debug_roi.py")
        elif choice == "11":
            print("🔧 启动环境检查...")
            run_command("python tools/simple_test.py")
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")
        print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
