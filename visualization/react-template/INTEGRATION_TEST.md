# 集成测试指南

## 端到端测试流程

### 1. 生成测试数据

#### 方式 1：使用测试脚本（推荐，无需依赖）

```bash
python3 test_json_export.py
```

这会生成 `test_strategy_report_data.json` 文件。

#### 方式 2：运行完整策略测试（需要安装依赖）

```bash
# 安装依赖
pip install pandas pytz matplotlib

# 运行策略测试
python3 test_strategy.py strategy/double_mean.py
```

这会生成：
- `double_mean_report_data.json` - JSON 数据文件
- `double_mean_report.html` - HTML 报告（如果安装了 matplotlib）

### 2. 启动 React 模板

```bash
cd visualization/react-template
npm install  # 如果还没安装依赖
npm run dev
```

浏览器会自动打开 http://localhost:5173

### 3. 加载数据

#### 方式 1：文件上传（推荐）

1. 在浏览器中点击"选择文件"按钮
2. 选择生成的 JSON 文件（如 `test_strategy_report_data.json`）
3. 数据会自动加载并显示

#### 方式 2：URL 参数

如果 JSON 文件在可访问的位置：

```
http://localhost:5173?data=http://localhost:8000/data/test_strategy_report_data.json
```

### 4. 验证功能

检查以下功能是否正常：

- [ ] K 线图表正常显示
- [ ] 图表支持缩放、平移、十字线
- [ ] 技术指标线（MA5、MA20）正常显示
- [ ] 买卖点标记正常显示
- [ ] 点击订单标记显示详细信息
- [ ] 统计面板显示正确数据
- [ ] 决策信息列表正常显示
- [ ] 点击决策显示详细信息

## 性能测试

### 大数据量测试

生成包含大量数据的 JSON 文件，测试性能：

```python
# 修改 test_json_export.py 增加数据量
bars_count = 1000  # 1000 根 K 线
orders_count = 100  # 100 个订单
```

### 浏览器兼容性测试

在不同浏览器中测试：
- Chrome/Edge (Chromium)
- Firefox
- Safari

## 数据格式兼容性测试

### 测试不同版本的数据格式

修改 `data_exporter.py` 中的 `DATA_FORMAT_VERSION`，测试向后兼容性。

### 测试缺失字段

创建包含部分字段的 JSON 文件，测试容错性。

## 常见问题

### Q: 图表不显示？

A: 检查：
1. 浏览器控制台是否有错误
2. JSON 数据格式是否正确
3. `bars` 数组是否为空

### Q: 数据加载失败？

A: 检查：
1. JSON 文件格式是否正确
2. 文件路径是否正确
3. 浏览器控制台错误信息

### Q: 性能问题？

A: 优化建议：
1. 减少数据量（采样）
2. 使用虚拟滚动
3. 优化图表渲染

