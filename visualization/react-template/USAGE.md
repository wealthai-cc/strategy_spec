# 使用指南

## 快速开始

### 1. 生成 JSON 数据

运行策略测试工具，会自动生成 JSON 数据文件：

```bash
python3 test_strategy.py strategy/double_mean.py
```

这会生成两个文件：
- `double_mean_report.html` - HTML 报告（过渡期保留）
- `double_mean_report_data.json` - JSON 数据文件（供 React 模板使用）

### 2. 启动 React 模板

```bash
cd visualization/react-template
npm install
npm run dev
```

浏览器会自动打开 http://localhost:5173

### 3. 加载数据

#### 方式 1：文件上传

1. 在浏览器中点击"选择文件"按钮
2. 选择生成的 JSON 数据文件（如 `double_mean_report_data.json`）
3. 数据会自动加载并显示

#### 方式 2：URL 参数

如果 JSON 文件在可访问的位置，可以通过 URL 参数加载：

```
http://localhost:5173?data=http://localhost:8000/data/double_mean_report_data.json
```

#### 方式 3：本地文件系统（开发环境）

修改 `vite.config.ts` 添加代理：

```typescript
server: {
  proxy: {
    '/data': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

然后通过 URL 参数加载：`?data=/data/double_mean_report_data.json`

## 功能说明

### K 线图表

- **缩放**：鼠标滚轮或手势缩放
- **平移**：拖拽图表平移
- **十字线**：鼠标移动显示十字线和数据点信息
- **技术指标**：自动显示 MA5、MA20 等技术指标线
- **买卖点标记**：在图表上标记订单位置

### 订单详情

- 点击订单列表中的订单，查看详细信息
- 显示订单价格、数量、类型、状态等
- 显示触发原因

### 策略决策

- 查看策略的所有决策记录
- 点击决策查看详细信息：
  - 技术指标值
  - 触发条件
  - 决策依据
  - 策略状态

### 统计面板

显示策略测试的统计信息：
- 总交易次数
- 买入/卖出次数
- K 线数量
- 决策次数

## 部署

### 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录。

### 静态文件部署

将 `dist/` 目录部署到任何 Web 服务器：

```bash
# 使用 Python 简单服务器
cd dist
python3 -m http.server 8000

# 使用 nginx
cp -r dist/* /var/www/html/
```

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

构建和运行：

```bash
docker build -t strategy-visualization .
docker run -p 8080:80 strategy-visualization
```

## 常见问题

### Q: 如何加载本地 JSON 文件？

A: 由于浏览器安全限制，不能直接加载本地文件系统。建议：
1. 使用文件上传功能
2. 启动一个简单的 HTTP 服务器提供 JSON 文件
3. 使用 URL 参数指向可访问的 JSON 文件

### Q: 图表不显示怎么办？

A: 检查：
1. JSON 数据格式是否正确
2. 浏览器控制台是否有错误
3. 数据中是否包含 `bars` 数组

### Q: 如何自定义样式？

A: 修改 `src/App.tsx` 中的内联样式，或创建 CSS 模块。

### Q: 如何添加更多技术指标？

A: 修改 `src/components/KLineChart.tsx` 中的 `calculateMA` 函数，添加新的指标计算逻辑。

## 数据格式

JSON 数据文件必须包含以下字段：

- `version`: 数据格式版本
- `metadata`: 元数据（策略名称、标的、时间等）
- `bars`: K 线数据数组
- `orders`: 订单数据数组
- `decisions`: 决策信息数组
- `statistics`: 统计信息

详细格式定义请参考 `src/types/data.ts`。



