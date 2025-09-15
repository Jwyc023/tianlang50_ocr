# -*- coding: utf-8 -*-
"""
日志分析工具 - 分析监控日志，诊断null数据问题
功能：
1. 解析日志文件
2. 统计识别失败情况
3. 分析失败原因
4. 生成诊断报告
"""

import os
import re
import glob
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

def find_latest_log() -> str:
    """查找最新的日志文件"""
    log_files = glob.glob("../data/logs/monitor_*.log")
    if not log_files:
        print("❌ 未找到日志文件！")
        return None
    
    latest_file = max(log_files, key=os.path.getmtime)
    print(f"📊 分析日志文件: {latest_file}")
    return latest_file

def parse_log_file(log_file: str) -> Dict:
    """解析日志文件"""
    print("📖 正在解析日志文件...")
    
    log_data = {
        'total_cycles': 0,
        'panel_stats': defaultdict(lambda: {'power_failures': 0, 'grade_failures': 0, 'total_attempts': 0}),
        'failure_reasons': defaultdict(int),
        'ocr_texts': defaultdict(list),
        'timestamps': [],
        'cycle_times': []
    }
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 解析时间戳
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                log_data['timestamps'].append(timestamp_match.group(1))
            
            # 解析循环信息
            if "开始第" in line and "次循环" in line:
                log_data['total_cycles'] += 1
            
            # 解析处理时间
            if "耗时:" in line:
                time_match = re.search(r'耗时: ([\d.]+)秒', line)
                if time_match:
                    log_data['cycle_times'].append(float(time_match.group(1)))
            
            # 解析板块处理结果
            for panel in PANEL_NAMES:
                if f"开始处理板块: {panel}" in line:
                    log_data['panel_stats'][panel]['total_attempts'] += 1
                
                if f"主力等级识别失败" in line and panel in line:
                    log_data['panel_stats'][panel]['power_failures'] += 1
                
                if f"级别识别失败" in line and panel in line:
                    log_data['panel_stats'][panel]['grade_failures'] += 1
            
            # 解析OCR原始文本
            if "主力等级识别:" in line:
                text_match = re.search(r"原始文本='([^']*)'", line)
                if text_match:
                    panel = extract_panel_from_context(line)
                    if panel:
                        log_data['ocr_texts'][f"{panel}_power"].append(text_match.group(1))
            
            if "级别识别:" in line:
                text_match = re.search(r"原始文本='([^']*)'", line)
                if text_match:
                    panel = extract_panel_from_context(line)
                    if panel:
                        log_data['ocr_texts'][f"{panel}_grade"].append(text_match.group(1))
            
            # 解析失败原因
            if "无效的ROI坐标" in line:
                log_data['failure_reasons']['无效ROI坐标'] += 1
            elif "不在ROI配置中" in line:
                log_data['failure_reasons']['ROI配置缺失'] += 1
            elif "处理时间过长" in line:
                log_data['failure_reasons']['处理超时'] += 1
    
    print(f"✓ 解析完成，共 {log_data['total_cycles']} 次循环")
    return log_data

def extract_panel_from_context(line: str) -> str:
    """从日志行中提取板块名称"""
    for panel in PANEL_NAMES:
        if panel in line:
            return panel
    return None

def analyze_panel_performance(log_data: Dict):
    """分析各板块性能"""
    print("\n=== 板块性能分析 ===")
    
    for panel in PANEL_NAMES:
        stats = log_data['panel_stats'][panel]
        total = stats['total_attempts']
        power_failures = stats['power_failures']
        grade_failures = stats['grade_failures']
        
        if total == 0:
            continue
        
        power_failure_rate = (power_failures / total) * 100
        grade_failure_rate = (grade_failures / total) * 100
        
        print(f"📊 {panel}:")
        print(f"   总尝试次数: {total}")
        print(f"   主力等级失败: {power_failures} ({power_failure_rate:.1f}%)")
        print(f"   级别失败: {grade_failures} ({grade_failure_rate:.1f}%)")
        
        # 给出建议
        if power_failure_rate > 50:
            print(f"   🔴 主力等级识别严重失败！")
        elif power_failure_rate > 20:
            print(f"   🟡 主力等级识别有问题")
        
        if grade_failure_rate > 50:
            print(f"   🔴 级别识别严重失败！")
        elif grade_failure_rate > 20:
            print(f"   🟡 级别识别有问题")

def analyze_ocr_texts(log_data: Dict):
    """分析OCR识别文本"""
    print("\n=== OCR文本分析 ===")
    
    for key, texts in log_data['ocr_texts'].items():
        if not texts:
            continue
        
        # 统计最常见的OCR结果
        text_counter = Counter(texts)
        most_common = text_counter.most_common(5)
        
        print(f"📝 {key} 最常见的OCR结果:")
        for text, count in most_common:
            percentage = (count / len(texts)) * 100
            print(f"   '{text}': {count}次 ({percentage:.1f}%)")
        
        # 分析空文本情况
        empty_count = texts.count('')
        if empty_count > 0:
            empty_rate = (empty_count / len(texts)) * 100
            print(f"   🔴 空文本: {empty_count}次 ({empty_rate:.1f}%)")

def analyze_performance(log_data: Dict):
    """分析性能数据"""
    print("\n=== 性能分析 ===")
    
    if log_data['cycle_times']:
        avg_time = sum(log_data['cycle_times']) / len(log_data['cycle_times'])
        max_time = max(log_data['cycle_times'])
        min_time = min(log_data['cycle_times'])
        
        print(f"📈 循环时间统计:")
        print(f"   平均时间: {avg_time:.2f}秒")
        print(f"   最大时间: {max_time:.2f}秒")
        print(f"   最小时间: {min_time:.2f}秒")
        
        # 统计超时情况
        timeout_count = sum(1 for t in log_data['cycle_times'] if t > 1.0)
        timeout_rate = (timeout_count / len(log_data['cycle_times'])) * 100
        
        if timeout_count > 0:
            print(f"   ⚠️ 超时次数: {timeout_count} ({timeout_rate:.1f}%)")
    
    # 分析失败原因
    if log_data['failure_reasons']:
        print(f"\n📊 失败原因统计:")
        for reason, count in log_data['failure_reasons'].items():
            print(f"   {reason}: {count}次")

def generate_diagnosis_report(log_data: Dict, log_file: str):
    """生成诊断报告"""
    report_file = f"../data/log_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== 日志分析报告 ===\n")
        f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"日志文件: {log_file}\n")
        f.write(f"总循环次数: {log_data['total_cycles']}\n\n")
        
        f.write("=== 板块性能统计 ===\n")
        for panel in PANEL_NAMES:
            stats = log_data['panel_stats'][panel]
            total = stats['total_attempts']
            if total > 0:
                power_rate = (stats['power_failures'] / total) * 100
                grade_rate = (stats['grade_failures'] / total) * 100
                f.write(f"{panel}: 主力等级失败率 {power_rate:.1f}%, 级别失败率 {grade_rate:.1f}%\n")
        
        f.write("\n=== OCR文本统计 ===\n")
        for key, texts in log_data['ocr_texts'].items():
            if texts:
                text_counter = Counter(texts)
                most_common = text_counter.most_common(3)
                f.write(f"{key}: {most_common}\n")
        
        f.write("\n=== 性能统计 ===\n")
        if log_data['cycle_times']:
            avg_time = sum(log_data['cycle_times']) / len(log_data['cycle_times'])
            f.write(f"平均循环时间: {avg_time:.2f}秒\n")
        
        f.write("\n=== 建议 ===\n")
        f.write("1. 检查失败率高的板块的ROI区域\n")
        f.write("2. 查看failed_screenshots目录中的截图\n")
        f.write("3. 重新校准ROI区域\n")
        f.write("4. 检查OCR识别质量\n")
    
    print(f"✓ 诊断报告已保存: {report_file}")

def main():
    """主函数"""
    print("=== 日志分析工具 ===")
    
    # 查找日志文件
    log_file = find_latest_log()
    if not log_file:
        return
    
    # 解析日志
    log_data = parse_log_file(log_file)
    
    # 分析板块性能
    analyze_panel_performance(log_data)
    
    # 分析OCR文本
    analyze_ocr_texts(log_data)
    
    # 分析性能
    analyze_performance(log_data)
    
    # 生成报告
    generate_diagnosis_report(log_data, log_file)
    
    print("\n=== 分析完成 ===")
    print("📁 生成的文件:")
    print("   - log_analysis_report_*.txt（分析报告）")
    print("💡 建议查看 failed_screenshots/ 目录中的截图")

if __name__ == "__main__":
    main()

