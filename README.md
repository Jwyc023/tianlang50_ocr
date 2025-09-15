# 天狼50多股同列监控系统

实时监控8个指数板块的主力等级和级别，自动判断做多/做空信号并保存到CSV文件。

## 📁 项目结构

```
tianlang50_multiSharesOneColumn/
├── src/                    # 核心监控脚本
│   ├── monitor.py          # 标准监控脚本（详细注释）
│   ├── monitor_fast.py     # 高性能监控脚本（并行处理）
│   └── monitor_with_logging.py # 带日志监控脚本（诊断null数据）
├── tools/                  # 工具脚本
│   ├── calibrate_rois.py   # ROI区域校准工具
│   ├── test_ocr.py         # OCR测试工具
│   ├── quick_test.py       # 快速测试工具
│   ├── simple_test.py      # 简单测试工具
│   ├── debug_roi.py        # ROI调试工具
│   └── screenshot_viewer.py # 截图查看工具
├── analysis/               # 数据分析工具
│   ├── analyze_csv.py      # 详细数据分析（含图表）
│   ├── quick_analyze.py    # 快速数据分析
│   ├── log_analyzer.py     # 日志分析工具（诊断null数据）
│   ├── analysis_charts/    # 分析图表
│   └── analysis_report_*.txt # 分析报告
├── data/                   # 数据文件
│   ├── rois.json          # ROI配置文件
│   ├── ticks_*.csv        # 监控数据CSV文件
│   ├── debug_images/       # 调试图像
│   ├── logs/              # 监控日志文件
│   └── failed_screenshots/ # 识别失败截图
├── docs/                   # 文档
│   ├── README.md          # 详细使用说明
│   └── DETAILS.md         # 技术细节说明
└── requirements.txt        # Python依赖包
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 校准ROI区域
```bash
python tools/calibrate_rois.py
```

### 3. 开始监控
```bash
# 标准版本（推荐学习）
python src/monitor.py

# 高性能版本（推荐生产）
python src/monitor_fast.py

# 带日志版本（诊断null数据）
python src/monitor_with_logging.py
```

### 4. 数据分析
```bash
# 快速分析
python analysis/quick_analyze.py

# 详细分析
python analysis/analyze_csv.py

# 日志分析（诊断null数据原因）
python analysis/log_analyzer.py
```

### 5. 诊断null数据问题
```bash
# 查看失败截图
python tools/screenshot_viewer.py

# 分析日志文件
python analysis/log_analyzer.py
```

## 📊 功能特点

- **实时监控**：每秒识别8个板块的主力等级和级别
- **智能判断**：自动生成做多/做空/观望信号
- **数据保存**：实时保存到CSV文件
- **性能优化**：支持并行处理，提高识别速度
- **调试工具**：完整的测试和调试工具链
- **数据分析**：可视化分析工具
- **问题诊断**：详细的日志记录和截图保存
- **null数据追踪**：自动记录识别失败的原因和截图

## 🎯 信号规则

- **做多**：≥7个正数主力等级 且 ≥3个A级及以上级别
- **做空**：≥7个负数主力等级 且 ≥3个-A级及以上级别
- **观望**：其他情况

## 📖 详细文档

- [使用说明](docs/README.md) - 详细的使用指南
- [技术细节](docs/DETAILS.md) - 代码原理和OCR配置

## 🛠️ 工具说明

| 工具 | 功能 | 使用场景 |
|------|------|----------|
| `calibrate_rois.py` | ROI校准 | 首次使用或界面变化时 |
| `test_ocr.py` | OCR测试 | 验证识别效果 |
| `debug_roi.py` | ROI调试 | 检查ROI区域准确性 |
| `quick_analyze.py` | 快速分析 | 诊断空数据问题 |
| `analyze_csv.py` | 详细分析 | 深度数据分析 |
| `monitor_with_logging.py` | 带日志监控 | 诊断null数据问题 |
| `log_analyzer.py` | 日志分析 | 分析null数据产生原因 |
| `screenshot_viewer.py` | 截图查看 | 查看识别失败截图 |

## ⚠️ 注意事项

1. 确保Tesseract OCR已正确安装
2. 监控页面需要最大化显示
3. 定期重新校准ROI区域
4. 建议使用高性能版本进行长时间监控

## 📞 技术支持

如遇问题，请按以下顺序排查：
1. 运行 `python tools/simple_test.py` 检查环境
2. 运行 `python tools/test_ocr.py` 测试OCR
3. 运行 `python analysis/quick_analyze.py` 分析数据质量
4. 查看 `docs/DETAILS.md` 了解技术细节