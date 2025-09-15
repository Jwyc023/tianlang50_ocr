# -*- coding: utf-8 -*-
"""
快速CSV分析工具 - 简单版本
专门用于快速诊断空数据问题
"""

import pandas as pd
import glob
import os
from datetime import datetime

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

def load_latest_csv():
	"""加载最新的CSV文件"""
    csv_files = glob.glob("../data/ticks_*.csv")
    if not csv_files:
        print("❌ 未找到CSV文件！")
        return None
    
    latest_file = max(csv_files, key=os.path.getmtime)
    print(f"📊 分析文件: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        print(f"✓ 数据行数: {len(df)}")
        return df
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None

def quick_analysis(df):
    """快速分析"""
    print("\n=== 快速诊断 ===")
    
    total_rows = len(df)
    
    # 统计每个板块的缺失情况
    print("📊 各板块数据缺失情况:")
    for name in PANEL_NAMES:
        power_col = f"{name}_主力等级"
        grade_col = f"{name}_级别"
        
        if power_col in df.columns and grade_col in df.columns:
            # 统计空值
            power_nan = df[power_col].isna().sum()
            power_empty = (df[power_col] == '').sum()
            power_total_missing = power_nan + power_empty
            
            grade_nan = df[grade_col].isna().sum()
            grade_empty = (df[grade_col] == '').sum()
            grade_total_missing = grade_nan + grade_empty
            
            power_rate = power_total_missing / total_rows * 100
            grade_rate = grade_total_missing / total_rows * 100
            
            print(f"  {name}:")
            print(f"    主力等级: {power_total_missing}/{total_rows} ({power_rate:.1f}%)")
            print(f"    级别: {grade_total_missing}/{total_rows} ({grade_rate:.1f}%)")
            
            # 给出建议
            if power_rate > 50:
                print(f"    🔴 主力等级识别严重失败！")
            elif power_rate > 20:
                print(f"    🟡 主力等级识别有问题")
            
            if grade_rate > 50:
                print(f"    🔴 级别识别严重失败！")
            elif grade_rate > 20:
                print(f"    🟡 级别识别有问题")
    
    # 分析信号分布
    if '结论' in df.columns:
        print(f"\n📊 信号分布:")
        signal_counts = df['结论'].value_counts()
        for signal, count in signal_counts.items():
            percentage = count / total_rows * 100
            print(f"  {signal}: {count} ({percentage:.1f}%)")
    
    # 分析时间间隔
    if 'timestamp' in df.columns:
        print(f"\n📊 时间分析:")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        time_diffs = df['timestamp'].diff().dt.total_seconds()
        avg_interval = time_diffs.mean()
        print(f"  平均时间间隔: {avg_interval:.1f}秒")
        
        if avg_interval > 2:
            print(f"  🟡 时间间隔过长，可能影响实时性")
        elif avg_interval < 0.5:
            print(f"  🟡 时间间隔过短，可能数据重复")

def generate_suggestions(df):
    """生成建议"""
    print(f"\n=== 问题诊断与建议 ===")
    
    total_rows = len(df)
    suggestions = []
    
    # 检查整体数据质量
    power_cols = [f"{name}_主力等级" for name in PANEL_NAMES if f"{name}_主力等级" in df.columns]
    grade_cols = [f"{name}_级别" for name in PANEL_NAMES if f"{name}_级别" in df.columns]
    
    total_power_missing = sum(df[col].isna().sum() + (df[col] == '').sum() for col in power_cols)
    total_grade_missing = sum(df[col].isna().sum() + (df[col] == '').sum() for col in grade_cols)
    
    total_possible = len(df) * len(PANEL_NAMES)
    power_missing_rate = total_power_missing / total_possible * 100
    grade_missing_rate = total_grade_missing / total_possible * 100
    
    print(f"📈 整体数据质量:")
    print(f"  主力等级缺失率: {power_missing_rate:.1f}%")
    print(f"  级别缺失率: {grade_missing_rate:.1f}%")
    
    # 给出建议
    if power_missing_rate > 30:
        suggestions.append("🔴 主力等级识别率过低！")
        suggestions.append("   建议:")
        suggestions.append("   1. 检查Tesseract OCR是否正确安装")
        suggestions.append("   2. 重新运行 calibrate_rois.py 调整ROI区域")
        suggestions.append("   3. 确保监控页面清晰显示")
        suggestions.append("   4. 尝试运行 python test_ocr.py 测试识别效果")
    
    if grade_missing_rate > 50:
        suggestions.append("🔴 级别识别率过低！")
        suggestions.append("   建议:")
        suggestions.append("   1. 级别文本可能太小或模糊")
        suggestions.append("   2. 重新校准ROI区域，选择更大的级别文本区域")
        suggestions.append("   3. 检查级别文本的字体和背景对比度")
    
    if power_missing_rate < 10 and grade_missing_rate < 20:
        suggestions.append("✅ 数据质量良好！")
        suggestions.append("   当前识别效果不错，可以继续使用")
    
    # 通用建议
    suggestions.append("💡 通用优化建议:")
    suggestions.append("   - 使用高性能版本: python monitor_fast.py")
    suggestions.append("   - 确保监控页面最大化且置顶")
    suggestions.append("   - 关闭不必要的窗口和特效")
    suggestions.append("   - 定期检查ROI区域是否准确")
    
    for suggestion in suggestions:
        print(suggestion)

def main():
    """主函数"""
    print("=== 快速CSV分析工具 ===")
    
    # 加载数据
    df = load_latest_csv()
    if df is None:
        return
    
    # 快速分析
    quick_analysis(df)
    
    # 生成建议
    generate_suggestions(df)
    
    print(f"\n=== 分析完成 ===")
    print("💡 如需更详细的分析，请运行: python analyze_csv.py")

if __name__ == "__main__":
    main()
