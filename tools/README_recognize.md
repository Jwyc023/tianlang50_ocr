# 单张截图识别程序

## 概述

这是一个使用`monitor_precision`中高精度识别方法的单张截图识别程序。它能够识别指定的截图文件，支持ROI区域识别和整个图片识别。

## 主要功能

- **高精度识别**: 使用`monitor_precision`中的多引擎融合识别方法
- **多种预处理方案**: 为数字和字母识别提供多种预处理算法
- **ROI支持**: 支持使用ROI配置文件识别特定区域
- **置信度评分**: 为每个识别结果提供置信度评分
- **调试图片保存**: 自动保存预处理后的图片用于调试
- **批量处理**: 支持批量识别多个截图文件

## 文件说明

- `recognize_single_image.py` - 主识别程序
- `recognize_example.py` - 使用示例和演示脚本

## 使用方法

### 1. 命令行使用

```bash
# 基本用法：识别指定图片
python tools/recognize_single_image.py /path/to/image.png

# 使用ROI配置识别
python tools/recognize_single_image.py /path/to/image.png -r ../data/rois.json

# 不保存调试图片
python tools/recognize_single_image.py /path/to/image.png --no-debug
```

### 2. 交互式使用

```bash
# 运行示例程序，提供交互式界面
python tools/recognize_example.py
```

### 3. 在代码中使用

```python
from recognize_single_image import recognize_single_image

# 识别单张图片
results = recognize_single_image(
    "screenshot.png",
    roi_config_path="../data/rois.json",
    save_debug=True
)

# 查看结果
if "error" not in results:
    print(f"识别结果: {results}")
else:
    print(f"识别失败: {results['error']}")
```

## 识别方法

程序使用`monitor_precision`中的高精度识别方法：

### 1. 多引擎融合识别
- 同时使用Tesseract、PaddleOCR、EasyOCR等多个OCR引擎
- 每个引擎尝试多种预处理方案
- 通过置信度评分选择最佳结果

### 2. 高级预处理
- **数字识别**: 4种预处理方案
  - 高倍放大 + 自适应阈值
  - Otsu阈值 + 形态学操作
  - CLAHE增强 + 双边滤波
  - 边缘检测 + 轮廓填充

- **字母识别**: 4种预处理方案
  - 超高倍放大 + 多级处理
  - CLAHE + 双边滤波 + Otsu
  - 边缘检测 + 形态学操作
  - 多尺度处理

### 3. 置信度评分
- 基于字符类型、长度、模式匹配等因素
- 数字识别和字母识别使用不同的评分标准
- 支持结果融合和纠错

## 输出结果

### 1. 控制台输出
- 详细的识别过程信息
- 各引擎和预处理方案的结果
- 最终识别结果和置信度

### 2. 返回结果字典
```python
{
    "image_path": "图片路径",
    "image_size": (高度, 宽度, 通道数),
    "ocr_engines": ["tesseract", "paddleocr", "easyocr"],
    "roi_results": {
        "板块名称": {
            "power": {
                "raw_text": "原始识别文本",
                "parsed_value": 解析后的数值,
                "confidence": 置信度
            },
            "grade": {
                "raw_text": "原始识别文本",
                "parsed_value": "解析后的级别",
                "confidence": 置信度
            }
        }
    },
    "full_image_results": {
        "numbers": {
            "text": "数字识别结果",
            "confidence": 置信度
        },
        "letters": {
            "text": "字母识别结果",
            "置信度": 置信度
        }
    }
}
```

### 3. 调试图片
如果启用调试模式，会在`debug_images/`目录下保存：
- `original.png` - 原始图片
- `{板块名}_power.png` - 主力等级ROI区域
- `{板块名}_grade.png` - 级别ROI区域

## 使用示例

### 示例1: 识别现有截图
```bash
# 识别最新的截图
python tools/recognize_example.py
# 选择选项1
```

### 示例2: 识别自定义图片
```bash
# 识别指定图片
python tools/recognize_single_image.py /path/to/your/image.png
```

### 示例3: 批量识别
```bash
# 批量识别多个截图
python tools/recognize_example.py
# 选择选项3
```

## 注意事项

1. **依赖要求**: 确保已安装所需的OCR依赖包
2. **图片格式**: 支持PNG、JPG、BMP、TIFF等常见格式
3. **ROI配置**: ROI配置文件格式需与`data/rois.json`一致
4. **处理时间**: 高精度识别需要较长时间，请耐心等待
5. **调试图片**: 调试图片会占用额外存储空间

## 故障排除

### 常见问题

1. **"没有可用的OCR引擎"**
   - 检查是否安装了pytesseract、paddleocr、easyocr
   - 检查Tesseract是否正确安装

2. **"无法加载图片文件"**
   - 检查图片文件是否存在
   - 检查图片格式是否支持

3. **识别结果不准确**
   - 检查图片质量是否良好
   - 尝试调整ROI坐标
   - 查看调试图片分析问题

4. **处理速度慢**
   - 这是正常现象，高精度识别需要时间
   - 可以禁用调试图片保存以提高速度

## 技术细节

程序基于`monitor_precision.py`中的以下核心方法：
- `multi_engine_recognize()` - 多引擎融合识别
- `ultra_preprocess_for_numbers()` - 数字预处理
- `ultra_preprocess_for_letters()` - 字母预处理
- `calculate_confidence()` - 置信度计算
- `select_best_result()` - 最佳结果选择
- `fuse_results()` - 结果融合
- `parse_power()` - 主力等级解析
- `normalize_grade()` - 级别规范化

