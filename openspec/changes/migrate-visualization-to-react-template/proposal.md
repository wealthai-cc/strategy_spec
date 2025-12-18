# Change: 将可视化图表迁移到 React 模板

## Why

当前可视化实现存在以下问题：

1. **每次生成新文件**：每次策略测试都会生成新的 HTML 文件，占用磁盘空间，不利于版本管理和对比
2. **静态 HTML 限制**：使用 matplotlib 生成静态图片嵌入 HTML，无法提供交互式体验（如缩放、筛选、数据钻取等）
3. **维护成本高**：HTML 模板硬编码在 Python 代码中，修改样式和布局需要修改代码并重新生成文件
4. **无法复用**：生成的 HTML 文件是独立的，无法作为模板复用，每次都需要重新生成完整文件

需要改进：
- 使用 React 实现可复用的可视化模板
- 数据与视图分离：只生成 JSON 数据文件，React 模板通过加载数据来显示
- 支持交互式图表（缩放、筛选、数据钻取等）
- 模板可以独立部署和维护，无需每次重新生成

## What Changes

- **REMOVED**: 静态 HTML 生成方式
  - 移除 `visualization/report_generator.py` 中的 HTML 模板硬编码
  - 移除 matplotlib 生成的 base64 图片嵌入方式
  - 移除每次测试生成独立 HTML 文件的方式

- **ADDED**: React 可视化模板
  - 创建独立的 React 应用作为可视化模板
  - 使用现代图表库（如 Recharts、ECharts React 或 TradingView Lightweight Charts）
  - 支持交互式 K 线图表（缩放、平移、十字线等）
  - 支持技术指标线叠加显示
  - 支持买卖点标记和详细信息展示
  - 支持数据筛选和钻取

- **ADDED**: JSON 数据导出
  - 修改 `visualization/data_collector.py` 支持导出 JSON 格式数据
  - 数据格式包含：K 线数据、订单数据、决策信息、技术指标等
  - 数据文件命名：`{strategy_name}_data.json`

- **ADDED**: 数据加载机制
  - React 模板支持通过 URL 参数或文件上传加载 JSON 数据
  - 支持本地文件系统加载（开发环境）
  - 支持 HTTP API 加载（生产环境）

- **MODIFIED**: 测试工具集成
  - 修改 `test_strategy.py` 只生成 JSON 数据文件，不生成 HTML
  - 提供启动 React 模板的命令或说明
  - 可选：提供简单的 HTTP 服务器用于加载数据

## Impact

- **Affected specs**: 
  - `strategy-testing` - 修改策略测试可视化规范
- **Affected code**: 
  - 修改 `visualization/data_collector.py`（添加 JSON 导出）
  - 修改 `visualization/report_generator.py`（改为数据导出器）
  - 新增 `visualization/react-template/` 目录（React 应用）
  - 修改 `test_strategy.py`（移除 HTML 生成，只生成 JSON）
- **Affected docs**: 
  - 更新测试工具使用文档
  - 添加 React 模板使用说明
  - 添加数据格式文档

## Design Considerations

### React 模板架构
- 使用 Create React App 或 Vite 作为基础框架
- 组件化设计：K 线图表组件、订单标记组件、统计面板组件等
- 状态管理：使用 React Context 或 Redux 管理数据状态
- 路由：支持多策略数据切换（可选）

### 数据格式设计
- JSON Schema 定义数据格式
- 向后兼容：支持现有数据收集器的数据结构
- 可扩展：支持未来新增的数据类型

### 部署方式
- 开发环境：本地运行 React 开发服务器
- 生产环境：可以打包为静态文件部署到 CDN 或 Web 服务器
- 数据加载：支持本地文件、HTTP API、WebSocket 等多种方式

### 性能考虑
- 大数据量处理：支持数据分页或虚拟滚动
- 图表渲染优化：使用 Canvas 或 WebGL 渲染大量数据点
- 懒加载：按需加载技术指标和决策信息

