#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析monitor_fast.py生成的CSV数据，检查异常值
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

def load_fast_csv():
    """加载最新的fast CSV文件"""
    csv_files = glob.glob("../data/ticks_fast_*.csv")
    if not csv_files:
        print("❌ 未找到fast CSV文件！")
        return None
    
    latest_file = max(csv_files, key=os.path.getmtime)
    print(f"📊 分析文件: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        return df, latest_file
    except Exception as e:
        print(f"❌ 读取CSV失败: {e}")
        return None, None

def analyze_data_quality(df):
    """分析数据质量"""
    print("\n=== 数据质量分析 ===")
    
    # 基本统计
    print(f"总记录数: {len(df)}")
    print(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    
    # 检查每个板块的数据
    for name in PANEL_NAMES:
        power_col = f"{name}_主力等级"
        grade_col = f"{name}_级别"
        
        if power_col in df.columns and grade_col in df.columns:
            # 主力等级分析
            power_data = pd.to_numeric(df[power_col], errors='coerce')
            power_nan = power_data.isna().sum()
            power_valid = len(power_data) - power_nan
            
            # 级别分析
            grade_data = df[grade_col]
            grade_empty = (grade_data == '').sum()
            grade_valid = len(grade_data) - grade_empty
            
            print(f"\n{name}:")
            print(f"  主力等级: {power_valid}/{len(df)} 有效 ({power_nan} 个NaN)")
            print(f"  级别: {grade_valid}/{len(df)} 有效 ({grade_empty} 个空值)")
            
            if power_valid > 0:
                print(f"  主力等级范围: {power_data.min():.2f} 到 {power_data.max():.2f}")
                print(f"  主力等级均值: {power_data.mean():.2f}")
            
            # 检查异常值
            if power_valid > 0:
                q1 = power_data.quantile(0.25)
                q3 = power_data.quantile(0.75)
                iqr = q3 - q1
                outliers = power_data[(power_data < q1 - 1.5*iqr) | (power_data > q3 + 1.5*iqr)]
                if len(outliers) > 0:
                    print(f"  ⚠️  发现 {len(outliers)} 个异常值: {outliers.tolist()}")

def find_suspicious_records(df):
    """查找可疑的记录"""
    print("\n=== 可疑记录分析 ===")
    
    suspicious_records = []
    
    for idx, row in df.iterrows():
        issues = []
        
        # 检查每个板块
        for name in PANEL_NAMES:
            power_col = f"{name}_主力等级"
            grade_col = f"{name}_级别"
            
            if power_col in df.columns and grade_col in df.columns:
                power_val = row[power_col]
                grade_val = row[grade_col]
                
                # 检查主力等级是否为异常值
                try:
                    power_num = float(power_val)
                    if abs(power_num) > 100:  # 假设正常范围在-100到100之间
                        issues.append(f"{name}主力等级异常: {power_num}")
                except:
                    if pd.notna(power_val) and power_val != '':
                        issues.append(f"{name}主力等级格式错误: {power_val}")
                
                # 检查级别是否为异常值
                if grade_val and grade_val not in ['C', 'B', 'A', 'AA', 'AAA', '-C', '-B', '-A', '-AA', '-AAA']:
                    issues.append(f"{name}级别异常: {grade_val}")
        
        if issues:
            suspicious_records.append({
                'index': idx,
                'timestamp': row['timestamp'],
                'issues': issues,
                'screenshot': row.get('截图文件', 'N/A')
            })
    
    if suspicious_records:
        print(f"发现 {len(suspicious_records)} 条可疑记录:")
        for record in suspicious_records[:10]:  # 只显示前10条
            print(f"\n记录 {record['index']} ({record['timestamp']}):")
            for issue in record['issues']:
                print(f"  - {issue}")
            if record['screenshot'] != 'N/A':
                print(f"  截图: {record['screenshot']}")
    else:
        print("✅ 未发现可疑记录")

def analyze_signal_patterns(df):
    """分析信号模式"""
    print("\n=== 信号模式分析 ===")
    
    if '结论' in df.columns:
        signal_counts = df['结论'].value_counts()
        print("信号分布:")
        for signal, count in signal_counts.items():
            percentage = count / len(df) * 100
            print(f"  {signal}: {count} 次 ({percentage:.1f}%)")
        
        # 检查信号变化频率
        signal_changes = (df['结论'] != df['结论'].shift()).sum()
        print(f"\n信号变化次数: {signal_changes}")
        print(f"平均变化间隔: {len(df) / signal_changes:.1f} 次循环")

def main():
    """主函数"""
    print("=== Fast CSV数据分析工具 ===")
    
    result = load_fast_csv()
    if result is None:
        return
    
    df, file_path = result
    
    # 执行分析
    analyze_data_quality(df)
    find_suspicious_records(df)
    analyze_signal_patterns(df)
    
    print(f"\n✅ 分析完成！")
    print(f"如需查看具体截图，请检查: ../data/fast_screenshots/")

if __name__ == "__main__":
    main()

