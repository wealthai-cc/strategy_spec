# 策略测试可视化模板

基于 React + TypeScript + TradingView Lightweight Charts 的策略测试可视化模板。

## 功能特性

- 📊 交互式 K 线图表（缩放、平移、十字线）
- 📈 技术指标线叠加（MA5、MA20 等）
- 🎯 买卖点标记和详细信息
- 📋 策略决策信息展示
- 📊 统计面板
- 📱 响应式设计

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录，可以部署到任何静态文件服务器。

## 使用方式

### 方式 1：文件上传

1. 运行开发服务器：`npm run dev`
2. 在浏览器中打开应用
3. 点击"选择文件"按钮，上传 JSON 数据文件

### 方式 2：URL 参数

在 URL 中添加 `data` 参数：

```
http://localhost:5173?data=path/to/data.json
```

### 方式 3：HTTP API

修改 `src/hooks/useDataLoader.ts` 中的 `loadFromUrl` 方法，支持从 API 加载数据。

## 数据格式

JSON 数据文件格式：

```json
{
  "version": "1.0.0",
  "metadata": {
    "strategy_name": "double_mean",
    "symbol": "000001.XSHE",
    "market_type": "A_STOCK",
    "test_start_time": "2025-12-16T10:00:00Z",
    "test_end_time": "2025-12-16T15:00:00Z",
    "timeframe": "1d"
  },
  "bars": [...],
  "orders": [...],
  "decisions": [...],
  "statistics": {...}
}
```

详细格式定义请参考 `src/types/data.ts`。

## 项目结构

```
src/
├── components/          # React 组件
│   ├── KLineChart.tsx  # K 线图表组件
│   ├── OrderMarkers.tsx # 订单标记组件
│   ├── StatisticsPanel.tsx # 统计面板组件
│   └── DecisionInfo.tsx # 决策信息组件
├── hooks/              # React Hooks
│   └── useDataLoader.ts # 数据加载 Hook
├── types/              # TypeScript 类型定义
│   └── data.ts         # 数据格式类型
├── utils/              # 工具函数
│   └── dataParser.ts   # 数据解析工具
├── App.tsx             # 主应用组件
└── main.tsx            # 入口文件
```

## 技术栈

- **React 19** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **TradingView Lightweight Charts** - 金融图表库

## 部署

### 静态文件部署

1. 构建：`npm run build`
2. 将 `dist/` 目录部署到 Web 服务器或 CDN

### Docker 部署（可选）

```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 开发

### 添加新组件

1. 在 `src/components/` 创建新组件
2. 在 `App.tsx` 中引入并使用

### 修改样式

- 全局样式：`src/index.css`
- 组件样式：使用内联样式或创建 CSS 模块

## 许可证

MIT
