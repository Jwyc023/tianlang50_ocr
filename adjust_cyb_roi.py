#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调整创业板指级别ROI区域
"""

import cv2
import numpy as np
import json
import os
import mss

def adjust_cyb_roi():
    """调整创业板指级别ROI"""
    print("=== 调整创业板指级别ROI ===")
    
    # 检查文件
    rois_file = "data/rois.json"
    if not os.path.exists(rois_file):
        print(f"❌ ROI文件不存在: {rois_file}")
        return
    
    # 加载ROI配置
    try:
        with open(rois_file, "r", encoding="utf-8") as f:
            rois = json.load(f)
        print("✓ ROI配置加载成功")
    except Exception as e:
        print(f"❌ ROI配置加载失败: {e}")
        return
    
    # 获取当前创业板指级别ROI
    if "创业板指" not in rois or "grade" not in rois["创业板指"]:
        print("❌ 创业板指级别ROI不存在")
        return
    
    current_roi = rois["创业板指"]["grade"]
    x, y, w, h = current_roi[0], current_roi[1], current_roi[2], current_roi[3]
    print(f"当前创业板指级别ROI: ({x}, {y}, {w}, {h})")
    
    # 截图
    print("正在截图...")
    with mss() as sct:
        monitor = sct.monitors[0]
        img = np.array(sct.grab(monitor))
        img = img[:, :, :3]
    
    # 显示当前ROI区域
    img_with_roi = img.copy()
    cv2.rectangle(img_with_roi, (x, y), (x + w, y + h), (0, 0, 255), 2)
    cv2.putText(img_with_roi, "Current ROI", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # 保存当前ROI区域
    debug_dir = "data/debug_roi_adjustment"
    os.makedirs(debug_dir, exist_ok=True)
    
    current_file = os.path.join(debug_dir, "cyb_grade_current_roi.png")
    cv2.imwrite(current_file, img_with_roi)
    print(f"✓ 已保存当前ROI图像: {current_file}")
    
    # 提取当前ROI区域
    current_region = img[y:y+h, x:x+w]
    region_file = os.path.join(debug_dir, "cyb_grade_current_region.png")
    cv2.imwrite(region_file, current_region)
    print(f"✓ 已保存当前ROI区域: {region_file}")
    
    # 建议调整方案
    print(f"\n=== ROI调整建议 ===")
    print(f"当前ROI: ({x}, {y}, {w}, {h})")
    print(f"建议调整方案:")
    print(f"1. 向右扩展: ({x-10}, {y}, {w+20}, {h})")
    print(f"2. 向下扩展: ({x}, {y-5}, {w}, {h+10})")
    print(f"3. 全面扩展: ({x-10}, {y-5}, {w+20}, {h+10})")
    
    # 生成调整后的ROI图像
    adjustments = [
        ("向右扩展", (x-10, y, w+20, h)),
        ("向下扩展", (x, y-5, w, h+10)),
        ("全面扩展", (x-10, y-5, w+20, h+10)),
    ]
    
    for name, (nx, ny, nw, nh) in adjustments:
        # 确保坐标在图像范围内
        nx = max(0, nx)
        ny = max(0, ny)
        nw = min(nw, img.shape[1] - nx)
        nh = min(nh, img.shape[0] - ny)
        
        # 创建调整后的图像
        adjusted_img = img.copy()
        cv2.rectangle(adjusted_img, (nx, ny), (nx + nw, ny + nh), (0, 255, 0), 2)
        cv2.putText(adjusted_img, f"Adjusted: {name}", (nx, ny - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 保存调整后的图像
        adjusted_file = os.path.join(debug_dir, f"cyb_grade_{name.replace(' ', '_')}.png")
        cv2.imwrite(adjusted_file, adjusted_img)
        print(f"✓ 已保存{name}图像: {adjusted_file}")
        
        # 提取调整后的区域
        adjusted_region = img[ny:ny+nh, nx:nx+nw]
        region_file = os.path.join(debug_dir, f"cyb_grade_{name.replace(' ', '_')}_region.png")
        cv2.imwrite(region_file, adjusted_region)
        print(f"✓ 已保存{name}区域: {region_file}")
    
    print(f"\n=== 手动调整步骤 ===")
    print(f"1. 查看生成的图像文件，选择最合适的ROI区域")
    print(f"2. 使用 calibrate_rois.py 重新框选创业板指级别区域")
    print(f"3. 确保ROI区域完全包含 '-A' 字符")
    print(f"4. 保存新的ROI配置")
    
    print(f"\n📁 调试文件保存在: {debug_dir}/")
    print(f"请查看生成的图像，选择最合适的ROI调整方案")

if __name__ == "__main__":
    adjust_cyb_roi()
