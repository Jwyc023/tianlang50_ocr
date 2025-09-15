# -*- coding: utf-8 -*-
"""
CSV数据分析工具 - 分析空数据产生的原因
功能：
1. 统计空数据分布
2. 分析OCR识别失败的原因
3. 提供调试建议
4. 生成分析报告
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import glob
from typing import Dict, List, Tuple

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

def load_latest_csv() -> pd.DataFrame:
	"""加载最新的CSV文件"""
    csv_files = glob.glob("../data/ticks_*.csv")
    if not csv_files:
        print("❌ 未找到CSV文件！请先运行监控脚本。")
        return None
    
    # 按修改时间排序，选择最新的
    latest_file = max(csv_files, key=os.path.getmtime)
    print(f"📊 加载CSV文件: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        print(f"✓ 成功加载 {len(df)} 行数据")
        return df
    except Exception as e:
        print(f"❌ 加载CSV文件失败: {e}")
        return None

def analyze_missing_data(df: pd.DataFrame) -> Dict:
    """分析空数据分布"""
    print("\n=== 空数据分析 ===")
    
    missing_stats = {}
    
    # 分析每个板块的主力等级和级别
    for name in PANEL_NAMES:
        power_col = f"{name}_主力等级"
        grade_col = f"{name}_级别"
        
        if power_col in df.columns and grade_col in df.columns:
            power_missing = df[power_col].isna().sum()
            grade_missing = df[grade_col].isna().sum()
            power_empty = (df[power_col] == '').sum()
            grade_empty = (df[grade_col] == '').sum()
            
            total_rows = len(df)
            power_missing_rate = (power_missing + power_empty) / total_rows * 100
            grade_missing_rate = (grade_missing + grade_empty) / total_rows * 100
            
            missing_stats[name] = {
                'power_missing': power_missing + power_empty,
                'grade_missing': grade_missing + grade_empty,
                'power_missing_rate': power_missing_rate,
                'grade_missing_rate': grade_missing_rate
            }
            
            print(f"📈 {name}:")
            print(f"   主力等级缺失: {power_missing + power_empty}/{total_rows} ({power_missing_rate:.1f}%)")
            print(f"   级别缺失: {grade_missing + grade_empty}/{total_rows} ({grade_missing_rate:.1f}%)")
    
    return missing_stats

def analyze_data_patterns(df: pd.DataFrame) -> Dict:
    """分析数据模式"""
    print("\n=== 数据模式分析 ===")
    
    patterns = {}
    
    # 分析主力等级的数据分布
    power_cols = [f"{name}_主力等级" for name in PANEL_NAMES if f"{name}_主力等级" in df.columns]
    grade_cols = [f"{name}_级别" for name in PANEL_NAMES if f"{name}_级别" in df.columns]
    
    # 统计有效数据
    valid_power_data = 0
    valid_grade_data = 0
    
    for col in power_cols:
        valid_count = df[col].notna().sum()
        valid_power_data += valid_count
    
    for col in grade_cols:
        valid_count = df[col].notna().sum()
        valid_grade_data += valid_count
    
    total_possible = len(df) * len(PANEL_NAMES)
    power_valid_rate = valid_power_data / total_possible * 100
    grade_valid_rate = valid_grade_data / total_possible * 100
    
    patterns['power_valid_rate'] = power_valid_rate
    patterns['grade_valid_rate'] = grade_valid_rate
    
    print(f"📊 主力等级有效数据率: {power_valid_rate:.1f}%")
    print(f"📊 级别有效数据率: {grade_valid_rate:.1f}%")
    
    # 分析信号分布
    if '结论' in df.columns:
        signal_counts = df['结论'].value_counts()
        print(f"\n📊 信号分布:")
        for signal, count in signal_counts.items():
            percentage = count / len(df) * 100
            print(f"   {signal}: {count} ({percentage:.1f}%)")
    
    return patterns

def analyze_time_patterns(df: pd.DataFrame) -> Dict:
    """分析时间模式"""
    print("\n=== 时间模式分析 ===")
    
    if 'timestamp' not in df.columns:
        print("❌ 未找到时间戳列")
        return {}
    
    # 转换时间戳
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    df['second'] = df['timestamp'].dt.second
    
    # 分析每小时的数据质量
    hourly_stats = df.groupby('hour').agg({
        'timestamp': 'count',
        **{f"{name}_主力等级": lambda x: x.notna().sum() for name in PANEL_NAMES if f"{name}_主力等级" in df.columns},
        **{f"{name}_级别": lambda x: x.notna().sum() for name in PANEL_NAMES if f"{name}_级别" in df.columns}
    })
    
    print("📊 每小时数据质量:")
    for hour in hourly_stats.index:
        total_rows = hourly_stats.loc[hour, 'timestamp']
        print(f"   {hour:02d}:00 - {total_rows} 行数据")
    
    return hourly_stats

def generate_visualizations(df: pd.DataFrame, missing_stats: Dict):
    """生成可视化图表"""
    print("\n=== 生成可视化图表 ===")
    
    # 创建图表目录
    if not os.path.exists("analysis_charts"):
        os.makedirs("analysis_charts")
    
    # 1. 空数据率对比图
    plt.figure(figsize=(12, 8))
    
    # 准备数据
    panels = list(missing_stats.keys())
    power_rates = [missing_stats[panel]['power_missing_rate'] for panel in panels]
    grade_rates = [missing_stats[panel]['grade_missing_rate'] for panel in panels]
    
    x = np.arange(len(panels))
    width = 0.35
    
    plt.bar(x - width/2, power_rates, width, label='主力等级缺失率', alpha=0.8)
    plt.bar(x + width/2, grade_rates, width, label='级别缺失率', alpha=0.8)
    
    plt.xlabel('板块')
    plt.ylabel('缺失率 (%)')
    plt.title('各板块数据缺失率对比')
    plt.xticks(x, panels, rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('analysis_charts/missing_data_rates.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 时间序列图
    if 'timestamp' in df.columns:
        plt.figure(figsize=(15, 10))
        
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 选择几个主要板块绘制时间序列
        main_panels = PANEL_NAMES[:4]  # 前4个板块
        
        for i, panel in enumerate(main_panels):
            plt.subplot(2, 2, i+1)
            
            power_col = f"{panel}_主力等级"
            if power_col in df.columns:
                # 只绘制有效数据
                valid_data = df[df[power_col].notna()]
                if len(valid_data) > 0:
                    plt.plot(valid_data['timestamp'], valid_data[power_col], 'b-', alpha=0.7)
                    plt.title(f'{panel} 主力等级时间序列')
                    plt.xlabel('时间')
                    plt.ylabel('主力等级')
                    plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('analysis_charts/time_series.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    print("✓ 图表已保存到 analysis_charts/ 目录")

def generate_debug_suggestions(missing_stats: Dict, patterns: Dict) -> List[str]:
    """生成调试建议"""
    print("\n=== 调试建议 ===")
    
    suggestions = []
    
    # 分析缺失率最高的板块
    max_missing_panel = max(missing_stats.keys(), 
                          key=lambda x: missing_stats[x]['power_missing_rate'] + missing_stats[x]['grade_missing_rate'])
    max_missing_rate = missing_stats[max_missing_panel]['power_missing_rate'] + missing_stats[max_missing_panel]['grade_missing_rate']
    
    if max_missing_rate > 50:
        suggestions.append(f"🔴 严重问题：{max_missing_panel} 板块缺失率超过50%")
        suggestions.append("   建议：重新运行 calibrate_rois.py 调整ROI区域")
    elif max_missing_rate > 20:
        suggestions.append(f"🟡 警告：{max_missing_panel} 板块缺失率超过20%")
        suggestions.append("   建议：检查ROI区域是否包含完整文本")
    
    # 分析整体数据质量
    if patterns['power_valid_rate'] < 80:
        suggestions.append("🔴 主力等级识别率过低")
        suggestions.append("   建议：")
        suggestions.append("   - 检查Tesseract OCR是否正确安装")
        suggestions.append("   - 尝试调整图像预处理参数")
        suggestions.append("   - 确保监控页面清晰显示")
    
    if patterns['grade_valid_rate'] < 60:
        suggestions.append("🔴 级别识别率过低")
        suggestions.append("   建议：")
        suggestions.append("   - 级别文本可能太小或模糊")
        suggestions.append("   - 尝试增大ROI区域")
        suggestions.append("   - 检查级别文本的字体和颜色")
    
    # 通用建议
    suggestions.append("💡 通用优化建议：")
    suggestions.append("   - 确保监控页面最大化显示")
    suggestions.append("   - 关闭不必要的窗口和特效")
    suggestions.append("   - 使用高性能版本：python monitor_fast.py")
    suggestions.append("   - 定期运行 test_ocr.py 检查识别效果")
    
    for suggestion in suggestions:
        print(suggestion)
    
    return suggestions

def save_analysis_report(missing_stats: Dict, patterns: Dict, suggestions: List[str]):
    """保存分析报告"""
    report_file = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== CSV数据分析报告 ===\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("=== 空数据统计 ===\n")
        for panel, stats in missing_stats.items():
            f.write(f"{panel}:\n")
            f.write(f"  主力等级缺失率: {stats['power_missing_rate']:.1f}%\n")
            f.write(f"  级别缺失率: {stats['grade_missing_rate']:.1f}%\n\n")
        
        f.write("=== 数据质量 ===\n")
        f.write(f"主力等级有效数据率: {patterns['power_valid_rate']:.1f}%\n")
        f.write(f"级别有效数据率: {patterns['grade_valid_rate']:.1f}%\n\n")
        
        f.write("=== 调试建议 ===\n")
        for suggestion in suggestions:
            f.write(f"{suggestion}\n")
    
    print(f"✓ 分析报告已保存: {report_file}")

def main():
    """主函数"""
    print("=== CSV数据分析工具 ===")
    
    # 加载数据
    df = load_latest_csv()
    if df is None:
        return
    
    # 分析空数据
    missing_stats = analyze_missing_data(df)
    
    # 分析数据模式
    patterns = analyze_data_patterns(df)
    
    # 分析时间模式
    time_patterns = analyze_time_patterns(df)
    
    # 生成可视化图表
    generate_visualizations(df, missing_stats)
    
    # 生成调试建议
    suggestions = generate_debug_suggestions(missing_stats, patterns)
    
    # 保存分析报告
    save_analysis_report(missing_stats, patterns, suggestions)
    
    print("\n=== 分析完成 ===")
    print("📁 生成的文件:")
    print("   - analysis_charts/ 目录（包含图表）")
    print("   - analysis_report_*.txt（分析报告）")

if __name__ == "__main__":
    main()
