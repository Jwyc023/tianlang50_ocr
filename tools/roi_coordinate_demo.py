#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI坐标演示工具
可视化展示ROI坐标系统的含义
"""

import cv2
import numpy as np

def create_coordinate_demo():
    """创建坐标系统演示图"""
    # 创建一个800x600的演示图像
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # 设置背景为深灰色
    img.fill(50)
    
    # 绘制坐标轴
    cv2.line(img, (50, 50), (50, 550), (255, 255, 255), 2)  # y轴
    cv2.line(img, (50, 550), (750, 550), (255, 255, 255), 2)  # x轴
    
    # 绘制坐标轴标签
    cv2.putText(img, "Y", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, "X", (720, 580), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, "(0,0)", (10, 570), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # 绘制网格线
    for i in range(0, 800, 50):
        cv2.line(img, (i, 50), (i, 550), (100, 100, 100), 1)
    for i in range(0, 600, 50):
        cv2.line(img, (50, i), (750, i), (100, 100, 100), 1)
    
    # 绘制坐标刻度
    for i in range(0, 800, 100):
        cv2.putText(img, str(i), (i, 570), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    for i in range(0, 600, 100):
        cv2.putText(img, str(i), (10, i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    return img

def draw_roi_example(img, x, y, width, height, color, label):
    """在图像上绘制ROI示例"""
    # 绘制矩形
    cv2.rectangle(img, (x, y), (x + width, y + height), color, 2)
    
    # 绘制四个角点
    cv2.circle(img, (x, y), 4, color, -1)  # 左上角
    cv2.circle(img, (x + width, y), 4, color, -1)  # 右上角
    cv2.circle(img, (x, y + height), 4, color, -1)  # 左下角
    cv2.circle(img, (x + width, y + height), 4, color, -1)  # 右下角
    
    # 绘制坐标标签
    cv2.putText(img, f"{label}: [{x}, {y}, {width}, {height}]", 
                (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # 绘制角点坐标
    cv2.putText(img, f"({x},{y})", (x - 30, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    cv2.putText(img, f"({x+width},{y})", (x + width - 30, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    cv2.putText(img, f"({x},{y+height})", (x - 30, y + height + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    cv2.putText(img, f"({x+width},{y+height})", (x + width - 30, y + height + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

def main():
    """主函数"""
    print("=== ROI坐标系统演示 ===")
    print("此工具将可视化展示ROI坐标的含义")
    
    # 创建演示图像
    img = create_coordinate_demo()
    
    # 绘制示例ROI
    examples = [
        (100, 100, 150, 80, (0, 255, 0), "示例1"),
        (300, 200, 120, 60, (0, 0, 255), "示例2"),
        (500, 150, 100, 100, (255, 0, 0), "示例3"),
    ]
    
    for x, y, width, height, color, label in examples:
        draw_roi_example(img, x, y, width, height, color, label)
    
    # 添加说明文字
    cv2.putText(img, "ROI坐标格式: [x, y, width, height]", 
                (200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    cv2.putText(img, "x,y: 左上角坐标  width: 宽度  height: 高度", 
                (180, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
    
    # 显示图像
    cv2.namedWindow("ROI坐标演示", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("ROI坐标演示", 900, 700)
    cv2.moveWindow("ROI坐标演示", 100, 100)
    
    cv2.imshow("ROI坐标演示", img)
    
    print("\n演示说明:")
    print("- 绿色、红色、蓝色框框代表不同的ROI区域")
    print("- 圆点标记矩形的四个角")
    print("- 坐标标签显示每个角的具体位置")
    print("- ROI格式: [x, y, width, height]")
    print("- 按任意键关闭演示窗口")
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n=== 坐标系统总结 ===")
    print("1. x, y: 矩形左上角的坐标")
    print("2. width: 矩形的宽度（向右延伸）")
    print("3. height: 矩形的高度（向下延伸）")
    print("4. 四个角的位置:")
    print("   - 左上角: (x, y)")
    print("   - 右上角: (x + width, y)")
    print("   - 左下角: (x, y + height)")
    print("   - 右下角: (x + width, y + height)")

if __name__ == "__main__":
    main()

