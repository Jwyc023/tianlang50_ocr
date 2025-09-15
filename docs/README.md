### 使用说明（Windows）

- **安装依赖**
```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

- **安装 Tesseract OCR**
  - Windows 可从 `https://github.com/UB-Mannheim/tesseract/wiki` 下载安装包。
  - 安装后如未自动加入 PATH，请在 `monitor.py` 顶部设置：
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

- **校准截图区域**
```bash
python calibrate_rois.py
```
按提示依次框选 8 个板块的“主力等级”与“级别”区域，程序会生成 `rois.json`。

- **开始监控并保存 CSV**
```bash
# 标准版本（详细注释，适合学习）
python monitor.py

# 高性能版本（并行处理，速度更快）
python monitor_fast.py
```
脚本每秒全屏截图 → OCR 解析 → 判断信号（做多/做空/观望）→ 逐行写入 `ticks_YYYYmmdd_HHMMSS.csv`。

- **判定规则**
  - 至少 7 个“主力等级”为正，且 ≥3 个“级别”为 A/AA/AAA → 做多。
  - 至少 7 个“主力等级”为负，且 ≥3 个“级别”为 -A/-AA/-AAA → 做空。
  - 否则观望。

- **数据分析工具**
```bash
# 快速分析CSV中的空数据问题
python quick_analyze.py

# 详细分析（包含图表）
python analyze_csv.py

# 调试ROI区域是否准确
python debug_roi.py
```

- **提示**
  - 建议把目标软件最大化置顶，以减少 OCR 误差。
  - 如识别不准，重新运行校准工具并适当放大 ROI。
  - 运行 `python test_ocr.py` 可以测试OCR识别效果并保存调试图像。
  - 监控脚本会每10秒保存一次调试图像到 `debug_images/` 目录。
  - 使用分析工具诊断空数据产生的原因。

