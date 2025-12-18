# Design: 将可视化迁移到 React 模板

## Context

当前可视化实现使用 matplotlib 生成静态图片，嵌入到硬编码的 HTML 模板中。每次策略测试都会生成一个新的 HTML 文件。这种方式存在以下问题：

1. 无法提供交互式体验
2. 每次生成新文件，占用空间
3. 模板维护困难
4. 无法复用

## Goals

1. **数据与视图分离**：只生成 JSON 数据文件，React 模板负责渲染
2. **交互式体验**：支持图表缩放、筛选、数据钻取等交互功能
3. **模板复用**：一个 React 模板可以加载不同的数据文件
4. **易于维护**：React 模板独立维护，不影响 Python 代码

## Non-Goals

- 不实现实时数据流（WebSocket）
- 不实现多策略对比功能（未来可扩展）
- 不实现策略回测对比（未来可扩展）

## Decisions

### 1. React 框架选择

**决策**：使用 Vite + React + TypeScript

**理由**：
- Vite 提供快速的开发体验和构建速度
- TypeScript 提供类型安全，减少错误
- React 生态成熟，图表库选择多

**替代方案**：
- Create React App：构建速度较慢
- Next.js：对于静态模板来说过于复杂

### 2. 图表库选择

**决策**：使用 TradingView Lightweight Charts（通过 React 封装）

**理由**：
- 专为金融图表设计，性能优秀
- 支持 K 线、技术指标、订单标记等所有需求
- 轻量级，适合嵌入
- 支持交互式操作（缩放、平移、十字线）

**替代方案**：
- Recharts：更适合通用图表，金融图表功能有限
- ECharts React：功能强大但体积较大
- Plotly.js：功能全面但学习曲线陡

### 3. 数据格式

**决策**：使用 JSON 格式，包含完整的数据结构

**数据结构**：
```json
{
  "metadata": {
    "strategy_name": "double_mean",
    "symbol": "000001.XSHE",
    "market_type": "A_STOCK",
    "test_start_time": "2025-12-16T10:00:00Z",
    "test_end_time": "2025-12-16T15:00:00Z",
    "timeframe": "1d"
  },
  "bars": [
    {
      "open_time": 1704067200000,
      "close_time": 1704153600000,
      "open": "10.50",
      "high": "10.80",
      "low": "10.40",
      "close": "10.70",
      "volume": "1000000"
    }
  ],
  "orders": [
    {
      "timestamp": 1704067200000,
      "direction": "BUY",
      "price": "10.60",
      "quantity": 1000,
      "order_id": "order_001"
    }
  ],
  "decisions": [
    {
      "timestamp": 1704067200000,
      "action": "BUY",
      "indicators": {
        "MA5": "10.55",
        "MA20": "10.45"
      },
      "trigger_condition": "close > MA5 * 1.01",
      "reason": "价格高于MA5 1%，买入信号"
    }
  ],
  "statistics": {
    "total_orders": 10,
    "buy_orders": 5,
    "sell_orders": 5,
    "total_profit": "500.00"
  }
}
```

### 4. 数据加载方式

**决策**：支持多种加载方式

1. **URL 参数**：`?data=path/to/data.json`
2. **文件上传**：用户上传 JSON 文件
3. **本地文件系统**：开发环境直接读取文件（需要 HTTP 服务器）
4. **HTTP API**：生产环境通过 API 获取数据

### 5. 项目结构

```
visualization/
├── react-template/          # React 应用
│   ├── src/
│   │   ├── components/      # React 组件
│   │   │   ├── KLineChart.tsx
│   │   │   ├── OrderMarkers.tsx
│   │   │   ├── StatisticsPanel.tsx
│   │   │   └── DecisionInfo.tsx
│   │   ├── hooks/           # React Hooks
│   │   │   ├── useDataLoader.ts
│   │   │   └── useChartData.ts
│   │   ├── types/           # TypeScript 类型定义
│   │   │   └── data.ts
│   │   ├── utils/           # 工具函数
│   │   │   └── dataParser.ts
│   │   └── App.tsx          # 主应用组件
│   ├── public/              # 静态资源
│   ├── package.json
│   └── vite.config.ts
├── data_collector.py        # 数据收集（修改：添加 JSON 导出）
├── data_exporter.py         # 数据导出器（新增）
└── report_generator.py      # 保留但改为调用数据导出器
```

## Risks / Trade-offs

### 风险 1：React 模板部署复杂度

**风险**：需要额外的构建和部署步骤

**缓解**：
- 提供详细的部署文档
- 提供 Docker 镜像（可选）
- 支持打包为静态文件，可以部署到任何 Web 服务器

### 风险 2：数据格式兼容性

**风险**：未来数据结构变更可能导致模板不兼容

**缓解**：
- 定义 JSON Schema 并版本化
- 数据导出器支持版本字段
- React 模板支持多版本数据格式（向后兼容）

### 风险 3：性能问题

**风险**：大量数据可能导致渲染性能问题

**缓解**：
- 使用虚拟滚动或数据分页
- 图表库使用 Canvas 渲染，性能优秀
- 支持数据采样（可选）

## Migration Plan

### 阶段 1：数据导出（向后兼容）
1. 修改 `data_collector.py` 添加 JSON 导出方法
2. 创建 `data_exporter.py` 专门负责数据导出
3. 修改 `test_strategy.py` 同时生成 JSON 和 HTML（过渡期）

### 阶段 2：React 模板开发
1. 搭建 React 项目结构
2. 实现基础 K 线图表组件
3. 实现订单标记组件
4. 实现统计面板组件
5. 实现数据加载功能

### 阶段 3：集成和测试
1. 测试数据加载和渲染
2. 测试交互功能
3. 性能测试和优化
4. 文档编写

### 阶段 4：迁移和清理
1. 修改 `test_strategy.py` 只生成 JSON
2. 移除 HTML 生成代码
3. 更新文档
4. 归档旧的可视化实现

## Open Questions

1. **是否需要支持多策略对比**？
   - 当前阶段：否
   - 未来可扩展：是

2. **是否需要支持实时数据更新**？
   - 当前阶段：否
   - 未来可扩展：是（通过 WebSocket）

3. **数据文件存储位置**？
   - 建议：`reports/{strategy_name}_{timestamp}.json`
   - 或：用户指定路径

