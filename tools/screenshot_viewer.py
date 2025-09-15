# -*- coding: utf-8 -*-
"""
截图查看工具 - 查看识别失败时保存的截图
功能：
1. 列出所有失败的截图
2. 按板块和类型分类显示
3. 提供截图对比功能
4. 生成截图分析报告
"""

import os
import glob
from datetime import datetime
from collections import defaultdict
import cv2
import numpy as np

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

def find_screenshot_files() -> Dict:
    """查找所有截图文件"""
    screenshot_dir = "../data/failed_screenshots"
    if not os.path.exists(screenshot_dir):
        print("❌ 截图目录不存在！")
        return {}
    
    files = glob.glob(f"{screenshot_dir}/*.png")
    if not files:
        print("❌ 未找到截图文件！")
        return {}
    
    # 按板块和类型分类
    categorized = defaultdict(lambda: defaultdict(list))
    
    for file in files:
        filename = os.path.basename(file)
        # 解析文件名: panel_type_field_timestamp.png
        parts = filename.replace('.png', '').split('_')
        if len(parts) >= 4:
            panel = parts[0]
            field_type = parts[1]  # power 或 grade
            image_type = parts[2]  # raw, processed, marked
            timestamp = parts[3]
            
            categorized[panel][field_type].append({
                'file': file,
                'type': image_type,
                'timestamp': timestamp
            })
    
    return categorized

def display_screenshot_info(categorized_files: Dict):
    """显示截图信息"""
    print("\n=== 截图文件统计 ===")
    
    total_files = 0
    for panel in PANEL_NAMES:
        if panel in categorized_files:
            panel_files = categorized_files[panel]
            power_files = len(panel_files.get('power', []))
            grade_files = len(panel_files.get('grade', []))
            
            if power_files > 0 or grade_files > 0:
                print(f"📊 {panel}:")
                print(f"   主力等级失败截图: {power_files} 个")
                print(f"   级别失败截图: {grade_files} 个")
                total_files += power_files + grade_files
    
    print(f"\n📈 总计: {total_files} 个失败截图")

def view_screenshots_by_panel(categorized_files: Dict, panel: str):
    """查看指定板块的截图"""
    if panel not in categorized_files:
        print(f"❌ 未找到 {panel} 的截图")
        return
    
    panel_files = categorized_files[panel]
    
    print(f"\n=== {panel} 截图详情 ===")
    
    # 显示主力等级截图
    if 'power' in panel_files:
        print("🔢 主力等级失败截图:")
        for file_info in panel_files['power']:
            print(f"   {file_info['type']}: {file_info['timestamp']}")
    
    # 显示级别截图
    if 'grade' in panel_files:
        print("📝 级别失败截图:")
        for file_info in panel_files['grade']:
            print(f"   {file_info['type']}: {file_info['timestamp']}")

def show_image_comparison(categorized_files: Dict, panel: str, field_type: str):
    """显示图像对比"""
    if panel not in categorized_files or field_type not in categorized_files[panel]:
        print(f"❌ 未找到 {panel} 的 {field_type} 截图")
        return
    
    files = categorized_files[panel][field_type]
    
    # 查找同一时间戳的三个图像
    timestamp_groups = defaultdict(list)
    for file_info in files:
        timestamp_groups[file_info['timestamp']].append(file_info)
    
    for timestamp, group in timestamp_groups.items():
        if len(group) >= 3:  # raw, processed, marked
            print(f"\n📸 {panel} {field_type} {timestamp} 对比:")
            
            # 读取图像
            images = {}
            for file_info in group:
                img = cv2.imread(file_info['file'])
                if img is not None:
                    images[file_info['type']] = img
            
            # 显示图像信息
            for img_type, img in images.items():
                height, width = img.shape[:2]
                print(f"   {img_type}: {width}x{height}")
            
            # 询问是否显示图像
            choice = input("是否显示图像对比？(y/n): ").strip().lower()
            if choice == 'y':
                display_images(images, f"{panel}_{field_type}_{timestamp}")

def display_images(images: Dict, title: str):
    """显示图像对比"""
    if not images:
        return
    
    # 调整图像大小以便显示
    max_height = 400
    resized_images = {}
    
    for img_type, img in images.items():
        height, width = img.shape[:2]
        if height > max_height:
            scale = max_height / height
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized_images[img_type] = cv2.resize(img, (new_width, new_height))
        else:
            resized_images[img_type] = img
    
    # 创建对比图像
    img_types = ['raw', 'processed', 'marked']
    available_images = [resized_images.get(t) for t in img_types if t in resized_images]
    
    if len(available_images) >= 2:
        # 水平拼接图像
        combined = np.hstack(available_images)
        cv2.imshow(f"对比: {title}", combined)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def generate_screenshot_report(categorized_files: Dict):
    """生成截图分析报告"""
    report_file = f"../data/screenshot_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== 截图分析报告 ===\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("=== 失败截图统计 ===\n")
        total_failures = 0
        for panel in PANEL_NAMES:
            if panel in categorized_files:
                panel_files = categorized_files[panel]
                power_files = len(panel_files.get('power', []))
                grade_files = len(panel_files.get('grade', []))
                
                if power_files > 0 or grade_files > 0:
                    f.write(f"{panel}: 主力等级失败 {power_files} 次, 级别失败 {grade_files} 次\n")
                    total_failures += power_files + grade_files
        
        f.write(f"\n总计失败次数: {total_failures}\n")
        
        f.write("\n=== 分析建议 ===\n")
        f.write("1. 查看 raw 图像：检查ROI区域是否包含完整文本\n")
        f.write("2. 查看 processed 图像：检查图像预处理效果\n")
        f.write("3. 查看 marked 图像：检查ROI区域位置\n")
        f.write("4. 对比不同时间戳的图像：分析识别一致性\n")
        f.write("5. 重新校准ROI区域：如果ROI不准确\n")
    
    print(f"✓ 截图分析报告已保存: {report_file}")

def main():
    """主函数"""
    print("=== 截图查看工具 ===")
    
    # 查找截图文件
    categorized_files = find_screenshot_files()
    if not categorized_files:
        return
    
    # 显示统计信息
    display_screenshot_info(categorized_files)
    
    # 生成报告
    generate_screenshot_report(categorized_files)
    
    # 交互式查看
    while True:
        print("\n=== 操作选项 ===")
        print("1. 查看指定板块的截图")
        print("2. 显示图像对比")
        print("3. 显示所有板块统计")
        print("0. 退出")
        
        choice = input("请选择操作 (0-3): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            print("\n可用板块:")
            for i, panel in enumerate(PANEL_NAMES, 1):
                if panel in categorized_files:
                    print(f"{i}. {panel}")
            
            try:
                panel_choice = int(input("选择板块编号: ")) - 1
                if 0 <= panel_choice < len(PANEL_NAMES):
                    panel = PANEL_NAMES[panel_choice]
                    view_screenshots_by_panel(categorized_files, panel)
            except ValueError:
                print("❌ 无效输入")
        
        elif choice == "2":
            print("\n可用板块:")
            for i, panel in enumerate(PANEL_NAMES, 1):
                if panel in categorized_files:
                    print(f"{i}. {panel}")
            
            try:
                panel_choice = int(input("选择板块编号: ")) - 1
                if 0 <= panel_choice < len(PANEL_NAMES):
                    panel = PANEL_NAMES[panel_choice]
                    field_type = input("选择类型 (power/grade): ").strip()
                    if field_type in ['power', 'grade']:
                        show_image_comparison(categorized_files, panel, field_type)
            except ValueError:
                print("❌ 无效输入")
        
        elif choice == "3":
            display_screenshot_info(categorized_files)
    
    print("👋 再见！")

if __name__ == "__main__":
    main()

