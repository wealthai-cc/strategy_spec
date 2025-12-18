# Tasks: 将可视化迁移到 React 模板

## 1. 数据导出功能

### 1.1 创建数据导出器
- [x] 创建 `visualization/data_exporter.py` 模块
- [x] 实现 `export_to_json()` 方法，将数据收集器的数据导出为 JSON
- [x] 定义 JSON Schema 数据结构
- [x] 支持数据版本化（添加 `version` 字段）
- [ ] 编写单元测试验证数据导出

### 1.2 修改数据收集器
- [x] 修改 `visualization/data_collector.py` 添加 JSON 导出接口
- [x] 确保数据结构完整（bars、orders、decisions、statistics）
- [x] 保持向后兼容（不影响现有功能）
- [ ] 编写单元测试

### 1.3 修改测试工具
- [x] 修改 `test_strategy.py` 添加 JSON 导出选项
- [x] 默认同时生成 JSON 和 HTML（过渡期）
- [ ] 添加命令行参数 `--json-only`（未来使用）
- [x] 更新使用文档

## 2. React 模板开发

### 2.1 项目初始化
- [x] 在 `visualization/` 下创建 `react-template/` 目录
- [x] 使用 Vite 初始化 React + TypeScript 项目
- [x] 配置项目依赖（React、TypeScript、TradingView Charts）
- [x] 配置构建和开发脚本
- [x] 添加 `.gitignore` 和 `README.md`

### 2.2 类型定义
- [x] 创建 `src/types/data.ts` 定义数据结构类型
- [x] 定义 `StrategyData`、`BarData`、`OrderData`、`DecisionInfo` 等类型
- [x] 确保类型与 JSON Schema 一致
- [x] 导出类型供组件使用

### 2.3 K 线图表组件
- [x] 创建 `src/components/KLineChart.tsx` 组件
- [x] 集成 TradingView Lightweight Charts
- [x] 实现 K 线数据渲染
- [x] 实现技术指标线叠加（MA5、MA20 等）
- [x] 实现交互功能（缩放、平移、十字线）
- [x] 添加图表配置选项（主题、颜色等）
- [ ] 编写组件测试

### 2.4 订单标记组件
- [x] 创建 `src/components/OrderMarkers.tsx` 组件
- [x] 在图表上标记买卖点
- [x] 实现 hover 提示框显示订单详情
- [x] 支持点击查看完整订单信息
- [x] 区分买入和卖出标记样式
- [ ] 编写组件测试

### 2.5 决策信息组件
- [x] 创建 `src/components/DecisionInfo.tsx` 组件
- [x] 显示策略决策的详细信息
- [x] 展示技术指标值
- [x] 展示触发条件
- [x] 展示决策依据
- [x] 支持时间轴浏览
- [ ] 编写组件测试

### 2.6 统计面板组件
- [x] 创建 `src/components/StatisticsPanel.tsx` 组件
- [x] 显示策略测试统计信息
- [x] 显示交易次数、盈亏等关键指标
- [x] 支持数据可视化（如饼图、柱状图）
- [x] 响应式布局设计
- [ ] 编写组件测试

### 2.7 数据加载功能
- [x] 创建 `src/hooks/useDataLoader.ts` Hook
- [x] 实现 URL 参数加载（`?data=path/to/data.json`）
- [x] 实现文件上传加载
- [x] 实现本地文件系统加载（开发环境）
- [x] 实现 HTTP API 加载
- [x] 添加加载状态和错误处理
- [ ] 编写 Hook 测试

### 2.8 主应用组件
- [x] 创建 `src/App.tsx` 主应用组件
- [x] 集成所有子组件
- [x] 实现数据加载和状态管理
- [x] 实现布局和样式
- [x] 添加加载和错误状态显示
- [ ] 编写应用测试

## 3. 样式和用户体验

### 3.1 样式设计
- [ ] 设计整体 UI 风格（参考现有 HTML 报告）
- [ ] 实现响应式布局（支持不同屏幕尺寸）
- [ ] 添加主题切换（亮色/暗色，可选）
- [ ] 优化移动端体验（可选）

### 3.2 交互优化
- [ ] 优化图表交互性能
- [ ] 添加加载动画
- [ ] 添加错误提示
- [ ] 添加数据为空状态显示

## 4. 集成和测试

### 4.1 端到端测试
- [x] 测试完整流程：Python 生成 JSON → React 加载显示
- [x] 创建测试脚本验证 JSON 导出功能
- [x] 创建集成测试指南
- [ ] 测试不同数据量下的性能（需要实际测试）
- [ ] 测试不同浏览器的兼容性（需要实际测试）
- [x] 测试数据格式兼容性（版本化支持）

### 4.2 文档编写
- [x] 编写 React 模板使用文档
- [x] 编写数据格式文档（JSON Schema）
- [x] 编写部署文档
- [x] 更新测试工具使用文档
- [x] 添加快速开始指南
- [x] 添加集成测试指南
- [ ] 添加示例和截图（需要实际运行截图）

## 5. 迁移和清理

### 5.1 过渡期支持
- [x] 保持 HTML 生成功能（向后兼容）
- [x] 添加配置选项选择生成方式（JSON 优先，HTML 可选）
- [x] 更新文档说明两种方式

### 5.2 完全迁移（未来）
- [ ] 修改 `test_strategy.py` 默认只生成 JSON
- [ ] 移除 HTML 生成代码
- [ ] 移除 matplotlib 依赖（如果不再需要）
- [ ] 更新所有相关文档

## 6. 部署和分发

### 6.1 构建配置
- [x] 配置生产环境构建
- [x] 优化构建产物大小（代码分割）
- [x] 配置环境变量（Vite 环境变量）

### 6.2 部署选项
- [x] 提供静态文件部署方案
- [x] 提供 Docker 镜像（Dockerfile + docker-compose.yml）
- [x] 提供 nginx 配置示例
- [x] 编写部署文档
- [ ] 提供 npm 包发布（可选，未来考虑）

