# 项目结构说明

## 📁 目录结构

```
tianlang50_multiSharesOneColumn/
├── 📁 src/                    # 核心监控脚本
│   ├── 📄 monitor.py          # 标准监控脚本（详细注释，适合学习）
│   └── 📄 monitor_fast.py     # 高性能监控脚本（并行处理，适合生产）
│
├── 📁 tools/                  # 工具脚本
│   ├── 📄 calibrate_rois.py   # ROI区域校准工具
│   ├── 📄 test_ocr.py         # OCR测试工具
│   ├── 📄 quick_test.py       # 快速测试工具
│   ├── 📄 simple_test.py      # 简单测试工具
│   └── 📄 debug_roi.py        # ROI调试工具
│
├── 📁 analysis/               # 数据分析工具
│   ├── 📄 analyze_csv.py      # 详细数据分析（含图表）
│   ├── 📄 quick_analyze.py    # 快速数据分析
│   ├── 📁 analysis_charts/    # 分析图表
│   │   ├── 📊 missing_data_rates.png
│   │   └── 📊 time_series.png
│   └── 📄 analysis_report_*.txt # 分析报告
│
├── 📁 data/                   # 数据文件
│   ├── 📄 rois.json          # ROI配置文件
│   ├── 📄 ticks_*.csv        # 监控数据CSV文件
│   └── 📁 debug_images/       # 调试图像（运行时生成）
│
├── 📁 docs/                   # 文档
│   ├── 📄 README.md          # 详细使用说明
│   └── 📄 DETAILS.md         # 技术细节说明
│
├── 📄 start_monitor.py        # 启动脚本（菜单式操作）
├── 📄 README.md              # 项目总览
├── 📄 PROJECT_STRUCTURE.md   # 项目结构说明（本文件）
└── 📄 requirements.txt       # Python依赖包
```

## 🎯 各目录功能说明

### 📁 src/ - 核心监控脚本
- **monitor.py**: 标准版本，包含详细中文注释，适合学习和理解
- **monitor_fast.py**: 高性能版本，使用并行处理，适合生产环境

### 📁 tools/ - 工具脚本
- **calibrate_rois.py**: ROI区域校准，首次使用必须运行
- **test_ocr.py**: OCR识别效果测试
- **quick_test.py**: 快速功能测试
- **simple_test.py**: 环境检查工具
- **debug_roi.py**: ROI区域调试和可视化

### 📁 analysis/ - 数据分析工具
- **quick_analyze.py**: 快速分析CSV数据，诊断空数据问题
- **analyze_csv.py**: 详细数据分析，生成图表和报告
- **analysis_charts/**: 存储分析生成的图表
- **analysis_report_*.txt**: 分析报告文件

### 📁 data/ - 数据文件
- **rois.json**: ROI配置文件，存储8个板块的坐标信息
- **ticks_*.csv**: 监控数据文件，包含实时识别结果
- **debug_images/**: 调试图像，用于分析OCR识别问题

### 📁 docs/ - 文档
- **README.md**: 详细使用说明和操作指南
- **DETAILS.md**: 技术细节说明，包含OCR配置和代码原理

## 🚀 使用流程

### 首次使用
1. 运行 `python start_monitor.py` 选择菜单操作
2. 选择 "8. 环境检查" 确保环境正常
3. 选择 "1. 校准ROI区域" 进行首次校准
4. 选择 "2. 测试OCR识别效果" 验证识别效果

### 日常使用
1. 选择 "3. 开始标准监控" 或 "4. 开始高性能监控"
2. 监控过程中数据自动保存到 `data/ticks_*.csv`
3. 使用 "5. 快速数据分析" 或 "6. 详细数据分析" 分析结果

### 问题排查
1. 使用 "7. 调试ROI区域" 检查ROI是否准确
2. 使用 "2. 测试OCR识别效果" 测试识别效果
3. 使用 "5. 快速数据分析" 分析数据质量

## 📝 文件说明

### 核心文件
- **start_monitor.py**: 主入口，提供菜单式操作界面
- **requirements.txt**: Python依赖包列表
- **rois.json**: ROI配置文件，存储校准结果

### 输出文件
- **ticks_*.csv**: 监控数据，包含时间戳、各板块数据、信号结论
- **analysis_report_*.txt**: 数据分析报告
- **debug_images/**: OCR调试图像

### 配置文件
- **rois.json**: ROI坐标配置，每个板块包含主力等级和级别两个区域

## 🔧 维护建议

1. **定期校准**: 界面变化时重新运行ROI校准
2. **数据备份**: 定期备份 `data/` 目录下的重要数据
3. **性能监控**: 使用高性能版本进行长时间监控
4. **问题诊断**: 遇到问题时使用相应的调试工具

## 📞 技术支持

- 查看 `docs/README.md` 了解详细使用方法
- 查看 `docs/DETAILS.md` 了解技术原理
- 使用 `tools/simple_test.py` 检查环境问题
- 使用 `analysis/quick_analyze.py` 分析数据问题

