# -*- coding: utf-8 -*-
"""
时间轴校准工具
帮助用户标定时间轴的起点、终点坐标
"""

import json
import os
import time

import pyautogui


def get_mouse_position():
    """获取当前鼠标位置"""
    return pyautogui.position()


def calibrate_timeline():
    """校准时间轴坐标"""
    print("=== 时间轴校准工具 ===\n")
    print("本工具将帮助你标定时间轴的位置参数")
    print("请按照提示操作\n")
    
    config = {
        "timeline": {},
        "time_range": {
            "start": "09:30",
            "end": "15:00"
        },
        "rois": {}
    }
    
    # 1. 标定时间轴起点（9:30）
    print("步骤 1: 标定时间轴起点（9:30位置）")
    print("请将鼠标移动到时间轴的 9:30 位置")
    input("按 Enter 键记录坐标...")
    start_pos = get_mouse_position()
    config["timeline"]["start_x"] = start_pos.x
    print(f"✓ 起点坐标: X={start_pos.x}, Y={start_pos.y}\n")
    
    # 2. 标定时间轴终点（15:00）
    print("步骤 2: 标定时间轴终点（15:00位置）")
    print("请将鼠标移动到时间轴的 15:00 位置")
    input("按 Enter 键记录坐标...")
    end_pos = get_mouse_position()
    config["timeline"]["end_x"] = end_pos.x
    print(f"✓ 终点坐标: X={end_pos.x}, Y={end_pos.y}\n")
    
    # 3. 使用起点的Y坐标作为时间轴Y坐标
    config["timeline"]["y"] = start_pos.y
    
    # 4. 标定监控区域（可选）
    print("步骤 3: 标定板块显示区域")
    print("请将鼠标移动到所有板块显示区域的【上边界】")
    input("按 Enter 键记录坐标...")
    top_pos = get_mouse_position()
    config["timeline"]["monitor_area_y1"] = top_pos.y
    print(f"✓ 上边界: Y={top_pos.y}\n")
    
    print("请将鼠标移动到所有板块显示区域的【下边界】")
    input("按 Enter 键记录坐标...")
    bottom_pos = get_mouse_position()
    config["timeline"]["monitor_area_y2"] = bottom_pos.y
    print(f"✓ 下边界: Y={bottom_pos.y}\n")
    
    # 5. 确认时间范围
    print("步骤 4: 确认时间范围")
    print(f"当前时间范围: {config['time_range']['start']} ~ {config['time_range']['end']}")
    change = input("是否需要修改？(y/n): ").strip().lower()
    if change == 'y':
        start_time = input("请输入起始时间（格式：HH:MM，如 09:30）: ").strip()
        end_time = input("请输入结束时间（格式：HH:MM，如 15:00）: ").strip()
        config["time_range"]["start"] = start_time
        config["time_range"]["end"] = end_time
        print(f"✓ 时间范围更新: {start_time} ~ {end_time}\n")
    
    # 6. 保存配置
    config_path = "../data/timeline_config.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n=== 校准完成 ===")
    print(f"✓ 配置已保存: {config_path}")
    print("\n配置摘要:")
    print(f"  时间轴起点: X={config['timeline']['start_x']}, Y={config['timeline']['y']}")
    print(f"  时间轴终点: X={config['timeline']['end_x']}, Y={config['timeline']['y']}")
    print(f"  监控区域: Y({config['timeline']['monitor_area_y1']} ~ {config['timeline']['monitor_area_y2']})")
    print(f"  时间范围: {config['time_range']['start']} ~ {config['time_range']['end']}")
    print(f"\n现在你可以运行监控脚本:")
    print(f"  cd src")
    print(f"  python monitor_timeline.py")


def test_calibration():
    """测试校准结果"""
    config_path = "../data/timeline_config.json"
    
    if not os.path.exists(config_path):
        print("❌ 未找到配置文件，请先运行校准")
        return
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    print("\n=== 测试校准结果 ===")
    print("鼠标将依次移动到以下位置，请确认是否正确:\n")
    
    timeline = config["timeline"]
    
    # 测试起点
    print("1. 时间轴起点（9:30）")
    input("按 Enter 开始...")
    pyautogui.moveTo(timeline["start_x"], timeline["y"], duration=0.5)
    print(f"   位置: ({timeline['start_x']}, {timeline['y']})")
    time.sleep(1)
    
    # 测试中点
    mid_x = (timeline["start_x"] + timeline["end_x"]) // 2
    print("\n2. 时间轴中点（约12:15）")
    input("按 Enter 开始...")
    pyautogui.moveTo(mid_x, timeline["y"], duration=0.5)
    print(f"   位置: ({mid_x}, {timeline['y']})")
    time.sleep(1)
    
    # 测试终点
    print("\n3. 时间轴终点（15:00）")
    input("按 Enter 开始...")
    pyautogui.moveTo(timeline["end_x"], timeline["y"], duration=0.5)
    print(f"   位置: ({timeline['end_x']}, {timeline['y']})")
    
    print("\n✓ 测试完成")
    correct = input("\n位置是否正确？(y/n): ").strip().lower()
    
    if correct != 'y':
        print("请重新运行校准工具进行调整")
    else:
        print("✓ 校准结果正确，可以开始使用监控脚本")


def main():
    """主函数"""
    print("\n时间轴校准工具\n")
    print("1. 校准时间轴坐标")
    print("2. 测试校准结果")
    print("0. 退出")
    
    choice = input("\n请选择: ").strip()
    
    if choice == "1":
        calibrate_timeline()
    elif choice == "2":
        test_calibration()
    else:
        print("退出")


if __name__ == "__main__":
    main()


