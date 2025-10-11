# -*- coding: utf-8 -*-
"""
鼠标移动演示脚本
展示如何缓慢移动鼠标并进行监控
"""

import time
import pyautogui

# 设置鼠标移动速度（更缓慢）
pyautogui.PAUSE = 0.1

def demo_mouse_movement():
    """演示鼠标缓慢移动"""
    print("=== 鼠标移动演示 ===\n")
    print("这个演示将展示鼠标如何缓慢移动")
    print("移动鼠标到屏幕左上角可中断\n")
    
    # 获取当前鼠标位置
    start_pos = pyautogui.position()
    print(f"起始位置: {start_pos}")
    
    print("\n准备开始演示...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("\n开始移动!\n")
    
    # 模拟水平移动（从左到右）
    print("1. 水平移动演示（缓慢）")
    start_x = 300
    end_x = 1500
    y = 600
    steps = 20  # 移动步数，越多越平滑
    
    for i in range(steps + 1):
        # 计算当前X坐标
        x = int(start_x + (end_x - start_x) * i / steps)
        
        # 缓慢移动到目标位置
        pyautogui.moveTo(x, y, duration=0.5)  # duration越大越慢
        
        print(f"  步骤 {i+1}/{steps+1}: 移动到 ({x}, {y})")
        time.sleep(0.3)  # 每次移动后暂停
    
    print("\n✓ 演示完成!")
    print(f"从 ({start_x}, {y}) 移动到 ({end_x}, {y})")
    
    # 返回起始位置
    print("\n返回起始位置...")
    pyautogui.moveTo(start_pos.x, start_pos.y, duration=1.0)

if __name__ == "__main__":
    try:
        demo_mouse_movement()
    except pyautogui.FailSafeException:
        print("\n中断: 鼠标移到左上角")
    except KeyboardInterrupt:
        print("\n用户中断")


