## ADDED Requirements

### Requirement: WebSocket 后台服务

Python SDK SHALL 提供 WebSocket 客户端作为后台服务，自动连接 WealthAI 行情服务并接收实时数据，策略无需直接调用 WebSocket API。

#### Scenario: WebSocket 服务自动启动

- **WHEN** SDK 初始化时检测到 WebSocket 配置（端点、订阅列表等）
- **THEN** SDK SHALL 自动启动 WebSocket 客户端
- **AND** SDK SHALL 建立 WebSocket 连接到配置的端点
- **AND** SDK SHALL 发送 CONNECT 消息，包含配置的交易对和周期
- **AND** SDK SHALL 等待服务端确认（CONNECTED 消息）
- **AND** SDK SHALL 开始接收行情推送数据

#### Scenario: 数据缓存更新

- **WHEN** WebSocket 客户端接收到行情数据推送
- **THEN** SDK SHALL 解析数据为 Bar 对象（与 `market_data.proto` 格式一致）
- **AND** SDK SHALL 将数据存储到全局缓存中
- **AND** SDK SHALL 按 `(symbol, timeframe)` 组织缓存数据
- **AND** SDK SHALL 保持数据的时间顺序（最早的在前，最新的在后）
- **AND** SDK SHALL 限制缓存大小（建议最多 1000 根 K 线，避免内存溢出）

#### Scenario: 策略透明访问数据

- **WHEN** 策略调用 `wealthdata.get_price('BTCUSDT', count=20, frequency='1h')`
- **THEN** SDK SHALL 通过数据适配器获取数据
- **AND** 数据适配器 SHALL 优先从 WebSocket 缓存读取数据
- **AND** 如果 WebSocket 缓存中有数据，SHALL 返回缓存中的数据
- **AND** 如果 WebSocket 缓存中没有数据，SHALL 从 Context 读取（回测场景）
- **AND** 策略 SHALL 无需感知数据来源，完全透明

### Requirement: 混合数据源适配器

Python SDK SHALL 扩展 `ContextDataAdapter` 为混合数据源适配器，优先从 WebSocket 缓存读取数据，如果没有则从 Context 读取。

#### Scenario: 混合数据源查询

- **WHEN** 策略通过 `wealthdata.get_price()` 或 `context.history()` 查询数据
- **THEN** `ContextDataAdapter.get_history()` SHALL 首先尝试从 WebSocket 缓存获取数据
- **AND** 如果 WebSocket 缓存中有足够的数据，SHALL 直接返回
- **AND** 如果 WebSocket 缓存中没有数据或数据不足，SHALL 从 Context 的 `_market_data_context` 获取
- **AND** 策略 SHALL 无需感知数据来源，自动使用最佳数据源

#### Scenario: 数据源优先级

- **WHEN** WebSocket 缓存和 Context 中都有数据
- **THEN** 适配器 SHALL 优先返回 WebSocket 缓存中的数据（实时数据优先）
- **AND** 如果 WebSocket 缓存中的数据不足，SHALL 补充 Context 中的数据
- **AND** 合并后的数据 SHALL 保持时间顺序

#### Scenario: 回测场景兼容

- **WHEN** 在回测场景中（没有 WebSocket 连接）
- **THEN** WebSocket 缓存 SHALL 为空
- **AND** 适配器 SHALL 自动回退到从 Context 读取数据
- **AND** 回测功能 SHALL 不受影响，完全兼容

### Requirement: WebSocket 配置管理

Python SDK SHALL 提供配置接口，允许系统配置 WebSocket 连接参数和订阅列表。

#### Scenario: 系统级配置

- **WHEN** 系统需要配置 WebSocket 连接
- **THEN** SDK SHALL 支持通过配置文件、环境变量或 API 配置以下参数：
  - WebSocket 端点：`wss://ws.wealthai.cc:18000/market_data`
  - 备用端口：`18001`, `18002`
  - csrf_token：认证令牌
  - market_type：市场类型（如 `binance-testnet`）
  - 订阅列表：需要订阅的交易对和周期列表
- **AND** SDK SHALL 在初始化时读取配置并启动 WebSocket 服务

#### Scenario: 默认配置

- **WHEN** 系统未指定配置参数
- **THEN** SDK SHALL 使用默认配置：
  - 端点：`wss://ws.wealthai.cc:18000/market_data`
  - 备用端口：`18001`, `18002`
  - csrf_token：从环境变量或配置文件读取
  - market_type：`binance-testnet`（测试环境）
- **AND** SDK SHALL 支持通过环境变量覆盖默认配置

#### Scenario: 订阅列表配置

- **WHEN** 系统需要配置订阅列表
- **THEN** SDK SHALL 支持通过以下方式配置：
  - 配置文件：YAML 或 JSON 格式
  - 环境变量：逗号分隔的交易对和周期
  - API 调用：`configure_websocket_subscriptions(symbols, resolutions)`（供策略管理系统使用）
- **AND** SDK SHALL 在配置更新后自动更新 WebSocket 订阅

### Requirement: 错误处理和异常

Python SDK SHALL 提供明确的异常类型和处理方式，帮助策略处理 WebSocket 相关错误。

#### Scenario: 连接失败异常

- **WHEN** WebSocket 连接失败（网络问题、服务不可用等）
- **THEN** SDK SHALL 抛出 `WebSocketConnectionError` 异常
- **AND** SDK SHALL 包含详细的错误信息（错误原因、重试次数等）
- **AND** SDK SHALL 在自动重连失败后通知策略

#### Scenario: 订阅失败异常

- **WHEN** 订阅请求被服务端拒绝或超时
- **THEN** SDK SHALL 抛出 `WebSocketSubscriptionError` 异常
- **AND** SDK SHALL 包含服务端返回的错误信息
- **AND** SDK SHALL 允许策略重试订阅

#### Scenario: 数据解析错误

- **WHEN** SDK 接收到格式错误的数据
- **THEN** SDK SHALL 记录错误日志
- **AND** SDK SHALL 跳过该条数据，继续接收后续数据
- **AND** SDK SHALL 不中断连接或回调机制

