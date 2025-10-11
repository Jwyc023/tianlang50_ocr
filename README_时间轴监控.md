# 时间轴监控工具 - 快速开始

## 简介

自动记录时间轴上每一分钟8个板块的主力等级和级别数据。

## 快速使用

### 1. 安装依赖

```bash
pip install pyautogui opencv-python numpy pytesseract mss pillow
```

### 2. 校准时间轴

首次使用前需要标定时间轴位置：

```bash
cd tools
python calibrate_timeline.py
```

选择"1. 校准时间轴坐标"，按提示操作：
- 将鼠标移到时间轴的9:30位置，按Enter
- 将鼠标移到时间轴的15:00位置，按Enter
- 标定板块显示区域的上下边界

### 3. 测试运行（推荐）

首次使用建议先测试，只采集5个时间点：

```bash
cd src
python monitor_timeline.py --test
```

确认准确后，再完整运行。

### 4. 完整运行

确保时间轴界面完整显示后：

```bash
cd src
python monitor_timeline.py
```

程序会自动：
- 移动鼠标沿时间轴从9:30到15:00
- 每分钟采集一次数据（约330个点）
- 保存到CSV文件

**高级选项**:
```bash
# 测试模式，采集10个点
python monitor_timeline.py --test --test-points 10

# 指定输出文件
python monitor_timeline.py --output ../data/my_data.csv
```

**中断方法**: 将鼠标移到屏幕左上角

## 输出结果

数据保存在 `data/timeline_日期时间.csv`

包含字段：
- 时间（HH:MM）
- 8个板块的主力等级和级别
- 信号（做多/做空/观望）

## 注意事项

1. 监控期间不要操作电脑
2. 保持界面稳定，不要遮挡
3. 完整采集约需10-15分钟

## 详细文档

参见：[时间轴监控使用说明.md](docs/时间轴监控使用说明.md)

## 常见问题

**Q: 鼠标位置不准？**  
A: 重新运行校准工具

**Q: OCR识别错误率高？**  
A: 检查ROI配置（运行 `tools/calibrate_rois.py`）

**Q: 程序运行慢？**  
A: 正常现象，OCR识别需要时间

---

**提示**: 首次使用建议测试采集几个时间点，确认准确后再完整运行。

