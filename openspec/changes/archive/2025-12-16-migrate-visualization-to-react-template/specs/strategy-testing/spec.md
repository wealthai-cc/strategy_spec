## MODIFIED Requirements

### Requirement: 策略测试可视化报告生成
策略测试工具 SHALL 生成可视化报告，展示策略执行结果、K线图表、买卖点标记和统计信息。

#### Scenario: 生成 JSON 数据文件
- **WHEN** 策略测试完成
- **THEN** 系统生成 JSON 格式的数据文件（`{strategy_name}_data.json`）
- **AND** 数据文件包含完整的测试数据（K线、订单、决策信息、统计信息）
- **AND** 数据文件格式符合 JSON Schema 定义

#### Scenario: 使用 React 模板加载数据
- **WHEN** 用户打开 React 可视化模板
- **THEN** 模板支持通过 URL 参数加载数据文件（`?data=path/to/data.json`）
- **AND** 模板支持文件上传方式加载数据
- **AND** 模板支持本地文件系统加载（开发环境）
- **AND** 模板支持 HTTP API 加载（生产环境）

#### Scenario: 交互式 K 线图表显示
- **WHEN** 数据加载完成
- **THEN** React 模板显示交互式 K 线图表
- **AND** 图表支持缩放、平移、十字线等交互操作
- **AND** 图表显示技术指标线（MA5、MA20 等）
- **AND** 图表标记买卖点位置

#### Scenario: 买卖点详细信息展示
- **WHEN** 用户 hover 或点击买卖点标记
- **THEN** 显示订单详细信息（价格、数量、时间等）
- **AND** 显示策略决策信息（技术指标值、触发条件、决策依据）
- **AND** 显示策略状态（持仓、可用资金等）

#### Scenario: 统计信息面板
- **WHEN** 数据加载完成
- **THEN** React 模板显示统计信息面板
- **AND** 显示总交易次数、买入次数、卖出次数
- **AND** 显示总盈亏、收益率等关键指标
- **AND** 支持数据可视化展示（如饼图、柱状图）

## ADDED Requirements

### Requirement: JSON 数据导出格式
策略测试工具 SHALL 支持将测试数据导出为标准化的 JSON 格式。

#### Scenario: 导出完整测试数据
- **WHEN** 策略测试完成
- **THEN** 系统导出包含以下数据的 JSON 文件：
  - 元数据（策略名称、交易品种、测试时间范围等）
  - K 线数据（OHLCV）
  - 订单数据（买卖点信息）
  - 决策信息（技术指标、触发条件、决策依据）
  - 统计信息（交易次数、盈亏等）
- **AND** JSON 文件格式符合预定义的 Schema

#### Scenario: 数据版本化
- **WHEN** 导出 JSON 数据
- **THEN** 数据文件包含 `version` 字段标识数据格式版本
- **AND** React 模板支持多版本数据格式（向后兼容）

### Requirement: React 可视化模板
系统 SHALL 提供基于 React 的可视化模板，用于加载和显示策略测试数据。

#### Scenario: 模板独立部署
- **WHEN** React 模板构建完成
- **THEN** 模板可以打包为静态文件
- **AND** 模板可以部署到任何 Web 服务器或 CDN
- **AND** 模板不依赖后端服务（数据通过文件或 API 加载）

#### Scenario: 数据加载方式
- **WHEN** 用户访问 React 模板
- **THEN** 模板支持以下数据加载方式：
  - URL 参数：`?data=path/to/data.json`
  - 文件上传：用户上传 JSON 文件
  - 本地文件系统：开发环境直接读取文件
  - HTTP API：生产环境通过 API 获取数据

#### Scenario: 交互式图表功能
- **WHEN** 用户在 React 模板中查看图表
- **THEN** 图表支持以下交互功能：
  - 缩放：鼠标滚轮或手势缩放
  - 平移：拖拽平移图表
  - 十字线：鼠标移动显示十字线和数据点信息
  - 时间范围选择：选择特定时间范围查看

#### Scenario: 响应式设计
- **WHEN** 用户在不同设备上访问 React 模板
- **THEN** 模板自适应不同屏幕尺寸
- **AND** 移动端提供优化的交互体验（可选）

## REMOVED Requirements

### Requirement: 静态 HTML 报告生成
**Reason**: 静态 HTML 报告每次生成新文件，无法复用，且无法提供交互式体验。改为使用 React 模板加载 JSON 数据的方式。

**Migration**: 
- 现有 HTML 报告生成功能在过渡期保留（向后兼容）
- 未来版本将完全移除 HTML 生成，只生成 JSON 数据
- 用户可以使用 React 模板加载历史 JSON 数据文件

