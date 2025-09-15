# -*- coding: utf-8 -*-
"""
ROI调试工具 - 检查ROI区域是否准确
功能：
1. 显示ROI区域在屏幕上的位置
2. 保存ROI区域的截图
3. 测试OCR识别效果
4. 提供ROI调整建议
"""

import json
import cv2
import numpy as np
import pytesseract
from mss import mss
import os
from datetime import datetime

PANEL_NAMES = [
    "中证1000", "中证500", "沪深300", "上证50",
    "上证指数", "深证成指", "科创50", "创业板指",
]

def load_rois():
	"""加载ROI配置"""
	try:
          with open("data/rois.json", "r", encoding="utf-8") as f:
			rois = json.load(f)
        print(f"✓ 加载ROI配置成功，包含 {len(rois)} 个板块")
        return rois
    except Exception as e:
        print(f"❌ 加载ROI配置失败: {e}")
        return None

def grab_fullscreen(sct):
    """全屏截图"""
    monitor = sct.monitors[0]
    img = np.array(sct.grab(monitor))
    return img[:, :, :3]

def draw_roi_rectangles(img, rois):
    """在图像上绘制ROI矩形"""
    img_with_rois = img.copy()
    
    colors = [
        (0, 255, 0),    # 绿色 - 主力等级
        (0, 0, 255),    # 红色 - 级别
    ]
    
    for name in PANEL_NAMES:
        if name in rois:
            # 绘制主力等级区域（绿色）
            x1, y1, w1, h1 = rois[name]["power"]
            cv2.rectangle(img_with_rois, (x1, y1), (x1+w1, y1+h1), colors[0], 2)
            cv2.putText(img_with_rois, f"{name}_P", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[0], 1)
            
            # 绘制级别区域（红色）
            x2, y2, w2, h2 = rois[name]["grade"]
            cv2.rectangle(img_with_rois, (x2, y2), (x2+w2, y2+h2), colors[1], 2)
            cv2.putText(img_with_rois, f"{name}_G", (x2, y2-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[1], 1)
    
    return img_with_rois

def test_roi_ocr(img, rois, name):
    """测试单个板块的OCR识别"""
    if name not in rois:
        return None, None
    
    x1, y1, w1, h1 = rois[name]["power"]
    x2, y2, w2, h2 = rois[name]["grade"]
    
    # 裁剪区域
    crop_power = img[y1:y1+h1, x1:x1+w1]
    crop_grade = img[y2:y2+h2, x2:x2+w2]
    
    # 简单的OCR测试
    try:
        # 主力等级识别
        gray_power = cv2.cvtColor(crop_power, cv2.COLOR_BGR2GRAY)
        gray_power = cv2.resize(gray_power, None, fx=2, fy=2)
        text_power = pytesseract.image_to_string(gray_power, config='--psm 7')
        
        # 级别识别
        gray_grade = cv2.cvtColor(crop_grade, cv2.COLOR_BGR2GRAY)
        gray_grade = cv2.resize(gray_grade, None, fx=3, fy=3)
        text_grade = pytesseract.image_to_string(gray_grade, config='--psm 8')
        
        return text_power.strip(), text_grade.strip()
    except Exception as e:
        print(f"OCR测试失败: {e}")
        return None, None

def save_roi_images(img, rois):
    """保存ROI区域的图像"""
    debug_dir = "roi_debug"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    for name in PANEL_NAMES:
        if name in rois:
            x1, y1, w1, h1 = rois[name]["power"]
            x2, y2, w2, h2 = rois[name]["grade"]
            
            # 保存主力等级区域
            crop_power = img[y1:y1+h1, x1:x1+w1]
            cv2.imwrite(f"{debug_dir}/{name}_power_{timestamp}.png", crop_power)
            
            # 保存级别区域
            crop_grade = img[y2:y2+h2, x2:x2+w2]
            cv2.imwrite(f"{debug_dir}/{name}_grade_{timestamp}.png", crop_grade)
    
    print(f"✓ ROI图像已保存到 {debug_dir}/ 目录")

def analyze_roi_quality(img, rois):
    """分析ROI质量"""
    print("\n=== ROI质量分析 ===")
    
    for name in PANEL_NAMES:
        if name in rois:
            x1, y1, w1, h1 = rois[name]["power"]
            x2, y2, w2, h2 = rois[name]["grade"]
            
            print(f"📊 {name}:")
            print(f"  主力等级区域: ({x1}, {y1}, {w1}, {h1}) - 面积: {w1*h1}")
            print(f"  级别区域: ({x2}, {y2}, {w2}, {h2}) - 面积: {w2*h2}")
            
            # 检查区域大小
            if w1*h1 < 100:
                print(f"  🟡 主力等级区域可能太小")
            if w2*h2 < 100:
                print(f"  🟡 级别区域可能太小")
            
            # 测试OCR
            text_power, text_grade = test_roi_ocr(img, rois, name)
            if text_power:
                print(f"  主力等级识别: '{text_power}'")
            else:
                print(f"  🔴 主力等级识别失败")
            
            if text_grade:
                print(f"  级别识别: '{text_grade}'")
            else:
                print(f"  🔴 级别识别失败")

def show_roi_overlay(img, rois):
    """显示ROI覆盖图"""
    img_with_rois = draw_roi_rectangles(img, rois)
    
    # 调整图像大小以适应屏幕
    height, width = img_with_rois.shape[:2]
    if width > 1920:
        scale = 1920 / width
        new_width = int(width * scale)
        new_height = int(height * scale)
        img_with_rois = cv2.resize(img_with_rois, (new_width, new_height))
    
    cv2.imshow("ROI调试 - 绿色=主力等级, 红色=级别", img_with_rois)
    print("📱 显示ROI覆盖图，按任意键继续...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def generate_roi_suggestions(rois):
    """生成ROI调整建议"""
    print("\n=== ROI调整建议 ===")
    
    suggestions = []
    
    for name in PANEL_NAMES:
        if name in rois:
            x1, y1, w1, h1 = rois[name]["power"]
            x2, y2, w2, h2 = rois[name]["grade"]
            
            # 检查区域大小
            if w1*h1 < 200:
                suggestions.append(f"🔴 {name} 主力等级区域太小 ({w1}x{h1})")
                suggestions.append("   建议：重新校准，选择更大的区域")
            
            if w2*h2 < 200:
                suggestions.append(f"🔴 {name} 级别区域太小 ({w2}x{h2})")
                suggestions.append("   建议：重新校准，选择更大的区域")
            
            # 检查区域位置
            if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
                suggestions.append(f"🔴 {name} ROI坐标有负数")
                suggestions.append("   建议：重新校准ROI区域")
    
    if not suggestions:
        suggestions.append("✅ ROI配置看起来正常")
        suggestions.append("   如果识别效果不好，可能是图像质量问题")
    
    suggestions.append("💡 通用建议:")
    suggestions.append("   - 确保监控页面最大化显示")
    suggestions.append("   - ROI区域应该包含完整的文本")
    suggestions.append("   - 避免选择包含背景干扰的区域")
    suggestions.append("   - 定期重新校准ROI区域")
    
    for suggestion in suggestions:
        print(suggestion)

def main():
    """主函数"""
    print("=== ROI调试工具 ===")
    
    # 加载ROI配置
    rois = load_rois()
    if rois is None:
        return
    
    # 截图
    with mss() as sct:
        print("📸 正在截图...")
        img = grab_fullscreen(sct)
        print(f"✓ 截图完成，图像尺寸: {img.shape}")
        
        # 显示ROI覆盖图
        show_roi_overlay(img, rois)
        
        # 分析ROI质量
        analyze_roi_quality(img, rois)
        
		# 保存ROI图像
		save_roi_images(img, rois)
		
		# 生成建议
		generate_roi_suggestions(rois)
	
	print(f"\n=== 调试完成 ===")
	print("📁 生成的文件:")
	print("   - roi_debug/ 目录（包含ROI区域截图）")
	print("💡 如果ROI区域不准确，请运行: python tools/calibrate_rois.py")

if __name__ == "__main__":
    main()
