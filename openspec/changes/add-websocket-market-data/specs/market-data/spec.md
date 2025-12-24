## ADDED Requirements

### Requirement: WebSocket 实时行情数据订阅

系统 SHALL 支持通过 WebSocket 连接订阅实时行情数据，策略可以通过 SDK 接口订阅指定的交易对和 K 线周期，并接收实时推送的行情数据。

#### Scenario: 策略订阅实时行情数据

- **WHEN** 策略调用 `subscribe_market_data()` 接口，指定交易对和 K 线周期
- **THEN** SDK SHALL 建立 WebSocket 连接到 WealthAI 行情服务
- **AND** SDK SHALL 发送 CONNECT 消息进行订阅
- **AND** SDK SHALL 等待服务端确认（CONNECTED 消息）
- **AND** SDK SHALL 开始接收并解析行情推送数据
- **AND** SDK SHALL 通过回调函数将数据传递给策略

#### Scenario: 自动重连机制

- **WHEN** WebSocket 连接断开（网络故障、服务端关闭等）
- **THEN** SDK SHALL 自动尝试重连
- **AND** SDK SHALL 使用指数退避策略（最多重试 3 次）
- **AND** SDK SHALL 在重连成功后自动重新发送订阅消息
- **AND** SDK SHALL 通知策略连接状态变化（通过状态回调）

#### Scenario: 多策略并发订阅

- **WHEN** 多个策略同时订阅不同的交易对和周期
- **THEN** SDK SHALL 支持多个策略共享同一个 WebSocket 连接
- **AND** SDK SHALL 合并所有订阅请求，发送统一的 CONNECT 消息
- **AND** SDK SHALL 将接收到的数据分发给对应的策略回调函数
- **AND** SDK SHALL 保证线程安全，避免数据竞争

#### Scenario: 订阅管理

- **WHEN** 策略需要添加新的订阅（新的交易对或周期）
- **THEN** SDK SHALL 支持动态添加订阅
- **AND** SDK SHALL 更新 CONNECT 消息并重新发送
- **WHEN** 策略需要移除订阅
- **THEN** SDK SHALL 支持移除订阅
- **AND** SDK SHALL 更新订阅列表（如果所有订阅都移除，可以关闭连接）

#### Scenario: 数据格式一致性

- **WHEN** SDK 接收到 WebSocket 推送的行情数据
- **THEN** SDK SHALL 将数据解析为与 `market_data.proto` 中定义的 `Bar` 结构一致的对象
- **AND** SDK SHALL 保证数据字段类型和格式与现有规范一致
- **AND** SDK SHALL 支持多分辨率 K 线数据（1m、3m、5m、15m、30m、1h、4h、1d、1w）

### Requirement: WebSocket 行情数据缓存

系统 SHALL 缓存最近接收的 WebSocket 行情数据，以便策略可以查询历史数据。

#### Scenario: 数据缓存查询

- **WHEN** 策略通过 DataAdapter 查询历史行情数据
- **THEN** SDK SHALL 从缓存中返回最近接收的数据
- **AND** SDK SHALL 支持查询指定交易对和周期的历史数据
- **AND** SDK SHALL 限制缓存大小，避免内存溢出（建议缓存最近 1000 根 K 线）

#### Scenario: 缓存更新

- **WHEN** SDK 接收到新的行情数据推送
- **THEN** SDK SHALL 自动更新缓存
- **AND** SDK SHALL 按交易对和周期分别缓存
- **AND** SDK SHALL 保持数据的时间顺序

### Requirement: WebSocket 连接状态查询

系统 SHALL 提供接口供策略查询 WebSocket 连接状态。

#### Scenario: 查询连接状态

- **WHEN** 策略调用连接状态查询接口
- **THEN** SDK SHALL 返回当前连接状态（连接中、已连接、断开、重连中）
- **AND** SDK SHALL 返回最后接收数据的时间戳
- **AND** SDK SHALL 返回连接错误信息（如果存在）

