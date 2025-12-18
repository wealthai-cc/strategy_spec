# 快速开始指南

## 5 分钟快速上手

### 步骤 1：生成测试数据

```bash
# 在项目根目录
python3 test_json_export.py
```

这会生成 `test_strategy_report_data.json` 文件。

### 步骤 2：启动 React 模板

```bash
cd visualization/react-template
npm install  # 首次运行需要
npm run dev
```

浏览器会自动打开 http://localhost:5173

### 步骤 3：加载数据

1. 点击"选择文件"按钮
2. 选择 `test_strategy_report_data.json`
3. 数据会自动加载并显示

## 完整流程示例

### 1. 运行策略测试（生成真实数据）

```bash
# 安装依赖（如果还没安装）
pip install pandas pytz matplotlib

# 运行策略测试
python3 test_strategy.py strategy/double_mean.py
```

这会生成：
- `double_mean_report_data.json` - JSON 数据
- `double_mean_report.html` - HTML 报告（可选）

### 2. 查看可视化

```bash
cd visualization/react-template
npm run dev
```

在浏览器中上传 `double_mean_report_data.json` 文件。

## 功能演示

### K 线图表

- **缩放**：鼠标滚轮
- **平移**：拖拽图表
- **十字线**：鼠标移动显示数据点
- **技术指标**：自动显示 MA5、MA20

### 订单详情

- 点击订单列表查看详细信息
- 显示价格、数量、类型、状态

### 策略决策

- 查看所有决策记录
- 点击决策查看技术指标、触发条件、决策依据

## 常见问题

**Q: 如何加载本地 JSON 文件？**

A: 使用文件上传功能，或通过 URL 参数：`?data=http://localhost:8000/data.json`

**Q: 图表不显示？**

A: 检查浏览器控制台，确保 JSON 数据格式正确。

**Q: 如何部署到生产环境？**

A: 运行 `npm run build`，将 `dist/` 目录部署到 Web 服务器。

## 下一步

- 查看 [USAGE.md](./USAGE.md) 了解详细使用说明
- 查看 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解部署选项
- 查看 [INTEGRATION_TEST.md](./INTEGRATION_TEST.md) 了解测试方法

