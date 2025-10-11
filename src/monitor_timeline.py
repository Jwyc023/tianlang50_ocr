# -*- coding: utf-8 -*-
"""
时间轴监控脚本
自动移动鼠标沿时间轴，记录每分钟8个板块的主力等级和级别
"""

import csv
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys

import cv2
import numpy as np
import pytesseract
import pyautogui
from mss import mss

# 导入现有的处理函数
sys.path.append(os.path.dirname(__file__))
from monitor_fast import (
    PANEL_NAMES, GRADES_ORDER, 
    fast_preprocess, fast_ocr, 
    parse_power, normalize_grade, 
    decide_signal, grade_rank
)

# 禁用pyautogui的安全暂停
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True  # 移动鼠标到左上角可中断


class TimelineConfig:
    """时间轴配置"""
    
    def __init__(self, config_path: str = "../data/timeline_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # 默认配置（需要用户自行标定）
            return {
                "timeline": {
                    "start_x": 100,  # 时间轴起点X坐标（9:30）
                    "end_x": 1800,   # 时间轴终点X坐标（15:00）
                    "y": 600,        # 时间轴Y坐标（固定高度）
                    "monitor_area_y1": 400,  # 监控区域上边界
                    "monitor_area_y2": 700   # 监控区域下边界
                },
                "time_range": {
                    "start": "09:30",
                    "end": "15:00"
                },
                "rois": {}  # 8个板块的ROI配置（使用现有的rois.json）
            }
    
    def save_config(self):
        """保存配置"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"✓ 配置已保存: {self.config_path}")


class TimelineMonitor:
    """时间轴监控器"""
    
    def __init__(self, config: TimelineConfig):
        self.config = config
        self.timeline_cfg = config.config["timeline"]
        self.time_cfg = config.config["time_range"]
        
        # 加载ROI配置
        self.rois = self.load_rois("../data/rois.json")
        
        # 计算时间点
        self.time_points = self.calculate_time_points()
        print(f"✓ 共需采集 {len(self.time_points)} 个时间点")
    
    def load_rois(self, path: str) -> Dict:
        """加载ROI配置"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def calculate_time_points(self) -> List[Tuple[str, int]]:
        """计算所有需要采集的时间点及其对应的X坐标"""
        start_time = datetime.strptime(self.time_cfg["start"], "%H:%M")
        end_time = datetime.strptime(self.time_cfg["end"], "%H:%M")
        
        # 计算总分钟数
        total_minutes = int((end_time - start_time).total_seconds() / 60)
        
        # 计算X坐标范围
        start_x = self.timeline_cfg["start_x"]
        end_x = self.timeline_cfg["end_x"]
        x_range = end_x - start_x
        
        # 生成时间点列表：每分钟对应一个X坐标
        time_points = []
        for i in range(total_minutes + 1):
            current_time = start_time + timedelta(minutes=i)
            time_str = current_time.strftime("%H:%M")
            
            # 计算X坐标（线性插值）
            x = int(start_x + (x_range * i / total_minutes))
            
            time_points.append((time_str, x))
        
        return time_points
    
    def move_mouse_to_time(self, x: int, slow_mode: bool = True):
        """移动鼠标到时间轴指定X坐标
        
        Args:
            x: 目标X坐标
            slow_mode: 是否使用缓慢移动模式
        """
        y = self.timeline_cfg["y"]
        
        if slow_mode:
            # 缓慢移动模式：更平滑，更容易观察
            pyautogui.moveTo(x, y, duration=0.5)  # 0.5秒完成移动
            time.sleep(0.5)  # 等待界面更新和稳定
        else:
            # 快速模式
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.3)  # 等待界面更新
    
    def capture_and_recognize(self, sct: mss) -> Tuple[List[float], List[str]]:
        """截图并识别8个板块的数据"""
        # 截取完整屏幕
        monitor = sct.monitors[0]
        img = np.array(sct.grab(monitor))
        img = img[:, :, :3]
        
        # 识别各板块
        powers = []
        grades = []
        
        for name in PANEL_NAMES:
            try:
                x1, y1, w1, h1 = self.rois[name]["power"]
                x2, y2, w2, h2 = self.rois[name]["grade"]
                
                # 裁剪ROI
                crop_power = img[y1:y1+h1, x1:x1+w1]
                crop_grade = img[y2:y2+h2, x2:x2+w2]
                
                # 预处理
                pp = fast_preprocess(crop_power, is_grade=False)
                pg = fast_preprocess(crop_grade, is_grade=True)
                
                # OCR
                txt_power = fast_ocr(pp, psm=7, is_grade=False)
                txt_grade = fast_ocr(pg, psm=8, is_grade=True)
                
                # 解析
                val_power = parse_power(txt_power)
                val_grade = normalize_grade(txt_grade)
                
                powers.append(val_power)
                grades.append(val_grade)
                
            except Exception as e:
                print(f"  ⚠️  {name} 识别失败: {e}")
                powers.append(float("nan"))
                grades.append("")
        
        return powers, grades
    
    def run(self, output_csv: str = None, test_mode: bool = False, test_points: int = 5, slow_mode: bool = True):
        """运行时间轴监控
        
        Args:
            output_csv: 输出CSV文件路径
            test_mode: 测试模式，只采集部分时间点
            test_points: 测试模式下采集的时间点数量
            slow_mode: 缓慢移动模式，移动更平滑易观察
        """
        if output_csv is None:
            output_csv = f"../data/timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # 测试模式：只采集部分时间点
        time_points_to_process = self.time_points
        if test_mode:
            # 均匀采样
            step = len(self.time_points) // test_points
            time_points_to_process = [self.time_points[i * step] for i in range(test_points)]
            print(f"\n⚠️  测试模式：只采集 {len(time_points_to_process)} 个时间点")
        
        print("\n=== 时间轴监控系统 ===")
        print(f"✓ 时间范围: {self.time_cfg['start']} ~ {self.time_cfg['end']}")
        print(f"✓ 时间轴坐标: X({self.timeline_cfg['start_x']} ~ {self.timeline_cfg['end_x']}), Y({self.timeline_cfg['y']})")
        print(f"✓ 采集点数: {len(time_points_to_process)}{' (测试模式)' if test_mode else ''}")
        print(f"✓ 移动模式: {'缓慢平滑' if slow_mode else '快速'}")
        print(f"✓ 输出文件: {output_csv}")
        print("\n准备开始...")
        print("提示: 移动鼠标到屏幕左上角可中断程序")
        
        # 倒计时
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        print("\n开始采集!\n")
        
        # 创建CSV文件
        header = ["时间"]
        for name in PANEL_NAMES:
            header += [f"{name}_主力等级", f"{name}_级别"]
        header += ["信号"]
        
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as fcsv:
            writer = csv.writer(fcsv)
            writer.writerow(header)
            
            with mss() as sct:
                for idx, (time_str, x) in enumerate(time_points_to_process):
                    try:
                        print(f"[{idx+1}/{len(time_points_to_process)}] {time_str}...", end=" ")
                        
                        # 移动鼠标（使用缓慢模式）
                        self.move_mouse_to_time(x, slow_mode=slow_mode)
                        
                        # 采集数据
                        powers, grades = self.capture_and_recognize(sct)
                        
                        # 判断信号
                        signal = decide_signal(powers, grades)
                        
                        # 写入CSV
                        row = [time_str]
                        for i in range(8):
                            row.append(powers[i])
                            row.append(grades[i])
                        row.append(signal)
                        
                        writer.writerow(row)
                        fcsv.flush()
                        
                        print(f"✓ {signal}")
                        
                    except pyautogui.FailSafeException:
                        print("\n\n中断: 鼠标移到左上角")
                        break
                    except Exception as e:
                        print(f"\n  ⚠️  错误: {e}")
                        # 写入空行
                        row = [time_str] + [float("nan")] * 16 + ["错误"]
                        writer.writerow(row)
                        fcsv.flush()
        
        print(f"\n✓ 采集完成! 数据已保存到: {output_csv}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="时间轴监控工具")
    parser.add_argument("--test", action="store_true", help="测试模式，只采集5个时间点")
    parser.add_argument("--test-points", type=int, default=5, help="测试模式下采集的时间点数量")
    parser.add_argument("--output", type=str, help="输出CSV文件路径")
    parser.add_argument("--fast", action="store_true", help="快速模式（不推荐，可能识别不准）")
    args = parser.parse_args()
    
    print("=== 时间轴监控工具 ===\n")
    
    # 加载配置
    config = TimelineConfig()
    
    # 检查配置是否已校准
    if not os.path.exists(config.config_path):
        print("❌ 未找到时间轴配置文件")
        print(f"请先运行校准工具: python tools/calibrate_timeline.py")
        return
    
    # 创建监控器
    monitor = TimelineMonitor(config)
    
    # 开始监控（默认使用缓慢模式）
    monitor.run(
        output_csv=args.output, 
        test_mode=args.test, 
        test_points=args.test_points,
        slow_mode=not args.fast  # 默认缓慢，--fast时才快速
    )


if __name__ == "__main__":
    main()

