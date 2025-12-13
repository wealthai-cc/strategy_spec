# 量化交易策略规范文档评审

## 📋 设计原则确认

本规范基于以下核心设计原则：
1. **无状态策略**：策略不保存任何内部状态，每次 `Exec` 调用都是独立的纯函数，仅根据 `ExecRequest` 的输入数据做出决策
2. **风控内部化**：策略的风控逻辑在策略内部实现并闭环，对外仅输出订单操作事件
3. **接口规范**：这是策略实现者需要遵循的接口契约，而非策略管理系统的接口

---

## ✅ 优点

1. **架构清晰**：采用 gRPC/Protobuf，适合微服务和跨语言实现
2. **核心要素完整**：覆盖订单、账户、行情和策略执行的基本概念
3. **触发机制合理**：定义了行情触发、风控触发、订单状态触发三种类型
4. **无状态设计优雅**：`Exec` 方法接收完整上下文，策略无需维护状态，易于测试和扩展

---

## ⚠️ 问题与改进建议

### **1. 语法错误（P0 - 必须修复）**

**位置：`order.proto:36`**
```protobuf
enm TimeInForceType {
    INVLAID_TIME_IN_FORCE_TYPE = 0;
```

**问题：**
- `enm` 应为 `enum`
- `INVLAID` 拼写错误，应为 `INVALID`

---

### **2. 时间字段单位不统一（P0 - 必须修复）**

**问题：**
- `Bar.open_time`, `Bar.close_time` 注释说明为"unix时间戳毫秒"
- `Order.create_ts`, `Order.update_ts` **未注明单位**
- `Indicator.timestamp` **未注明单位**

**建议：**
- 统一所有时间字段为 **unix 毫秒时间戳**
- 在每个时间字段注释中明确标注"（unix毫秒时间戳）"

**影响范围：**
- `order.proto`: `Order.create_ts`, `Order.update_ts`
- `market_data.proto`: `Indicator.timestamp`

---

### **3. StrategySpec 服务方法是否完备？**

**当前方法：**
- `Health`: 健康探测
- `Exec`: 策略执行

**分析：基于无状态设计，当前方法已经足够**
- ✅ **无需 `Initialize`**：策略是无状态的，不需要初始化阶段
- ✅ **无需 `Shutdown`**：无状态策略无需清理资源
- ✅ **无需 `GetStrategyState`**：策略不维护状态，状态由调用方管理
- ✅ **无需 `UpdateConfig`**：配置变更可通过重新部署策略实现
- ✅ **无需风控接口**：风控在策略内部实现，通过 `ExecResponse` 的订单事件体现

**结论：当前 `StrategySpec` 服务的方法设计符合无状态策略的架构原则，无需增加额外方法。**

---

### **3.1 SDK 接口约定（TradingRule 与 佣金费率）**
- TradingRule 与 佣金费率均由策略侧通过 SDK 在本地查询获取，方法手册详见 `protocol/strategyspec/python_sdk.md`
- 调用开销：本地读取与解析描述文件，无网络请求，毫秒级（带缓存可达微秒级）
- 作用：用于下单参数合法性校验、成本与风控计算

---

### **4. 数据模型不完整（P1 - 强烈建议）**

#### **4.1 `ExecRequest` 缺少关键信息**

**当前缺失：**
1. **交易所元数据**
   - 交易对规格（最小下单量、最小价格变动单位、价格精度、数量精度）
   - 手续费率（Maker/Taker）
   - 杠杆倍数限制
   - 交易时间规则（开盘/收盘时间、是否支持24小时交易）

2. **当前时间戳**
   - 服务端当前时间（用于计算延迟、判断行情新鲜度）
   - 建议增加：`int64 current_timestamp = 7; // 服务端当前时间（unix毫秒时间戳）`

3. **触发事件详情**
   - 当 `trigger_type = RISK_MANAGE_TRIGGER_TYPE` 时，缺少具体的风控事件类型（强平预警？保证金不足？）
   - 当 `trigger_type = ORDER_STATUS_TRIGGER_TYPE` 时，缺少触发该调用的订单ID

**建议：**
```protobuf
message ExecRequest {
    int64 max_timeout = 1;
    TriggerType trigger_type = 2;
    repeated MarketDataContext market_data_context = 3;
    Account account = 4;
    repeated Order incomplete_orders = 5;
    repeated Order completed_orders = 6;
    int64 current_timestamp = 7; // 服务端当前时间（unix毫秒时间戳）
    TradingRule trading_rule = 8; // 交易规则（交易对规格、手续费率等）
    TriggerDetail trigger_detail = 9; // 触发事件的详细信息
}

message TradingRule {
    string symbol = 1; // 品种代号
    double min_quantity = 2; // 最小下单量
    double quantity_step = 3; // 数量步进
    double min_price = 4; // 最小价格
    double price_tick = 5; // 价格最小变动单位
    int32 price_precision = 6; // 价格精度（小数位数）
    int32 quantity_precision = 7; // 数量精度（小数位数）
    double maker_fee_rate = 8; // Maker手续费率
    double taker_fee_rate = 9; // Taker手续费率
    double max_leverage = 10; // 最大杠杆倍数
}

message TriggerDetail {
    string triggered_order_id = 1; // 触发此次调用的订单ID（仅当trigger_type=ORDER_STATUS_TRIGGER_TYPE时有效）
    string risk_event_type = 2; // 风控事件类型（仅当trigger_type=RISK_MANAGE_TRIGGER_TYPE时有效，如"margin_call"/"liquidation_warning"）
    string description = 3; // 事件描述
}
```

#### **4.2 `Order` 消息字段问题**

**问题1：价格字段语义混乱**
```protobuf
Currency price = 7; // 价格（当OrderType含Market时，该值无效）
Currency limit_price = 8; // limit价格（在OrderType含limit时）
Currency stop_price = 14; // 触发价（止损/止盈）
```

**分析：**
- `LIMIT_ORDER_TYPE`：只需要 `limit_price`，但 `price` 字段会误导
- `MARKET_ORDER_TYPE`：不需要任何价格字段
- `STOP_MARKET_ORDER_TYPE`：只需要 `stop_price`
- `STOP_LIMIT_ORDER_TYPE`：需要 `stop_price` 和 `limit_price`

**建议：移除 `price` 字段，统一使用 `limit_price` 和 `stop_price`**

---

**问题2：缺少关键字段**

当前缺失：
- `string client_order_id`：客户端订单ID（与交易所的 `order_id` 区分，用于关联策略侧订单）
- `Currency commission`：已支付手续费
- `string commission_asset`：手续费币种
- `Currency avg_fill_price`：平均成交价格（而非 `cummulative_quote_qty / executed_size`）
- `int64 last_fill_time`：最后成交时间（unix毫秒时间戳）
- `bool reduce_only`：只减仓标志（期货合约中重要参数，防止反向开仓）
- `string cancel_reason`：撤单原因（当 `status = CANCELED` 或 `REJECTED` 时）

**建议在 `Order` 消息中增加这些字段。**

#### **4.3 `Account` 缺少关键风控指标**

**当前缺失：**
```protobuf
message Account {
    string account_id = 1;
    AccountType account_type = 2;
    repeated Balance balances = 3;
    repeated Position positions = 4;
    // 缺少以下字段：
    // Currency total_net_value = 5; // 总资产净值（NAV）
    // Currency available_margin = 6; // 可用保证金
    // double margin_ratio = 7; // 保证金率（维持保证金/总资产净值）
    // double risk_level = 8; // 风险度（0-100，越高越危险）
    // double leverage = 9; // 当前使用的杠杆倍数
}
```

**建议：增加账户级别的风控指标，便于策略进行资金管理和风险评估。**

#### **4.4 `MarketDataContext` 扩展性不足**

**问题1：只支持K线数据**

缺少：
- **Tick数据**（逐笔成交，对高频策略重要）
- **OrderBook深度数据**（盘口买卖档位，对做市策略重要）
- **资金费率**（期货合约特有，影响持仓成本）
- **未平仓合约量（Open Interest）**（衡量市场活跃度）

**建议：**
```protobuf
message MarketDataContext {
    string timeframe = 1;
    repeated Bar bars = 2;
    repeated Indicator indicators = 3;
    repeated Tick ticks = 4; // Tick数据（可选）
    OrderBook order_book = 5; // 盘口深度（可选）
    double funding_rate = 6; // 资金费率（期货合约，可选）
    double open_interest = 7; // 未平仓合约量（可选）
}

message Tick {
    int64 timestamp = 1; // unix毫秒时间戳
    string price = 2;
    string quantity = 3;
    bool is_buyer_maker = 4; // 是否为买方是Maker
}

message OrderBook {
    int64 timestamp = 1; // unix毫秒时间戳
    repeated PriceLevel bids = 2; // 买单盘口
    repeated PriceLevel asks = 3; // 卖单盘口
}

message PriceLevel {
    string price = 1;
    string quantity = 2;
}
```

---

**问题2：技术指标扩展性差**

当前只支持 MA 和 EMA，无法灵活扩展。

**建议：**
```protobuf
message Indicator {
    int64 timestamp = 1; // unix毫秒时间戳
    map<string, double> indicators = 2; // 动态指标，如 {"MA_5": 100.5, "EMA_20": 102.3, "RSI_14": 65.2}
}
```

或使用 `oneof` 支持强类型：
```protobuf
message Indicator {
    int64 timestamp = 1;
    oneof indicator_type {
        MAIndicator ma = 2;
        EMAIndicator ema = 3;
        RSIIndicator rsi = 4;
        MACDIndicator macd = 5;
        // 可持续扩展
    }
}
```

---

### **5. 错误处理机制不完善（P1）**

#### **5.1 `ExecResponse` 缺少错误反馈**

**问题：**
策略执行失败（如计算异常、输入数据非法）时，无法返回错误信息。

**当前设计：**
```protobuf
message ExecResponse {
    repeated OrderOpEvent order_op_event = 1;
}
```

**建议：**
```protobuf
enum ExecutionStatus {
    SUCCESS = 0; // 执行成功
    PARTIAL_SUCCESS = 1; // 部分成功（部分订单生成失败）
    FAILED = 2; // 执行失败
}

message ExecResponse {
    ExecutionStatus status = 1; // 执行状态
    repeated OrderOpEvent order_op_event = 2; // 订单操作事件
    string error_message = 3; // 错误消息（当status=FAILED时）
    repeated string warnings = 4; // 警告信息（非致命问题）
}
```

#### **5.2 `HealthResponse` 应规范化错误码**

**当前设计：**
```protobuf
message HealthResponse {
    int32 code = 1; // 策略健康状态码，0 为健康，非 0 为不健康
    string message = 2; // 不健康原因
}
```

**建议：定义明确的健康状态码**
```protobuf
enum HealthStatus {
    HEALTHY = 0; // 健康
    DEGRADED = 1; // 降级（部分功能不可用）
    UNHEALTHY = 2; // 不健康
}

message HealthResponse {
    HealthStatus status = 1; // 健康状态
    string message = 2; // 状态描述
    repeated string details = 3; // 详细信息（如具体哪个依赖不可用）
}
```

---

### **6. 幂等性与并发说明缺失（P1）**

#### **6.1 订单幂等性规则不明确**

**`Order.unique_id` 的问题：**
- 幂等性保证的时长未说明（24小时？7天？永久？）
- 重复提交同一 `unique_id` 的订单应该如何处理？（拒绝？返回已有订单？）

**建议：在注释中明确说明**
```protobuf
string unique_id = 11; // 订单唯一幂等ID，24小时内重复提交将被拒绝（防重下单用）
```

#### **6.2 并发模型未定义**

**问题：**
- 策略实例是否支持并发调用 `Exec`？
- 如果不支持，调用方需要做串行化保证

**建议：在 `strategy_spec.proto` 文件头部或 `StrategySpec` 服务注释中说明：**
```protobuf
// StrategySpec 策略规范接口
// 
// 并发模型：策略实现必须是无状态的，但同一策略实例的 Exec 调用应由调用方保证串行化。
// 即：调用方需确保前一次 Exec 调用返回后，才能发起下一次 Exec 调用。
service StrategySpec {
    rpc Health(google.protobuf.Empty) returns (HealthResponse);
    rpc Exec(ExecRequest) returns (ExecResponse);
}
```

---

### **7. 文档与示例缺失（P2）**

**缺少：**
1. **策略执行流程图**：从触发事件 → `Exec` 调用 → 订单生成 → 订单执行 → 状态更新的完整链路
2. **不同触发类型的处理示例**：
   - 行情触发：如何根据 K线和技术指标生成交易信号
   - 订单状态触发：如何处理订单成交、拒绝、撤销
   - 风控触发：如何应对强平预警
3. **订单状态机**：订单状态之间的合法转换关系
4. **数据范围建议**：
   - `ExecRequest.completed_orders` 应该提供多长时间的历史订单？（建议：最近24小时）
   - `MarketDataContext.bars` 应该提供多少根K线？（建议：根据策略需求，默认500根）

**建议：增加独立的 `USAGE.md` 或 `EXAMPLES.md` 文件。**

---

### **8. 扩展性考虑（P2）**

#### **8.1 多品种策略支持**

**当前限制：**
- 注释说"只支持执行单品种下的同步策略"
- `ExecRequest.market_data_context` 是 `repeated`，理论上可支持多品种，但缺少品种标识

**问题：**
- `MarketDataContext` 没有 `symbol` 字段，无法区分是哪个品种的行情
- 多品种套利策略（如期现套利、跨品种对冲）无法实现

**建议：**
```protobuf
message MarketDataContext {
    string symbol = 1; // 品种代号（新增）
    string timeframe = 2;
    repeated Bar bars = 3;
    repeated Indicator indicators = 4;
}
```

如果短期不支持多品种策略，建议在注释中明确说明原因和未来规划。

#### **8.2 交易所差异性**

**问题：**
不同交易所的订单类型、状态、字段差异很大（如币安、OKX、Bybit），当前设计缺少交易所适配机制。

**建议：**
- 方案1：增加 `string exchange_type` 字段（如 "binance"/"okx"/"bybit"）
- 方案2：增加扩展字段 `map<string, string> exchange_specific`（存储交易所特有参数）

**示例：**
```protobuf
message Order {
    // ... 现有字段 ...
    string exchange_type = 20; // 交易所类型（如 "binance"）
    map<string, string> exchange_specific = 21; // 交易所特定字段（如 Binance的 "newOrderRespType"）
}
```

---

## 🎯 改进建议优先级

### **P0（必须修复）**
~~1. ✅ 修复语法错误（`order.proto:36` 的 `enm` 和 `INVLAID`）~~
~~2. ✅ 统一所有时间字段为 unix 毫秒时间戳，并在注释中明确标注~~

### **P1（强烈建议）**
3. 补充 `ExecRequest` 缺失字段：
   - ~~`current_timestamp`（当前时间）~~
   - ~~`TradingRule`（交易规则，策略通过SDK自取）~~
   - ~~`TriggerDetail`（触发事件详情）~~
4. 补充 `Order` 缺失字段：
   - `client_order_id`, `commission`, `avg_fill_price`, `last_fill_time`, `reduce_only`, `cancel_reason`
   - ~~移除语义混乱的 `price` 字段~~
~~5. 补充 `Account` 风控指标：~~
   - ~~`total_net_value`, `available_margin`, `margin_ratio`, `risk_level`, `leverage`~~
~~6. 完善 `ExecResponse` 错误处理：~~
   - ~~增加 `ExecutionStatus` 和 `error_message` 字段~~
~~7. 规范化 `HealthResponse` 错误码：~~
   - ~~使用 `HealthStatus` 枚举~~
~~8. 明确订单幂等性和并发模型~~
   - ~~系统保证同账户同策略顺序执行；增加 `ExecRequest.exec_id` 去重~~

### **P2（可选优化）**
9. 扩展 `MarketDataContext`：
   - 支持 Tick、OrderBook、资金费率、OI
   - 改进技术指标扩展性（使用 `map` 或 `oneof`）
~~10. 支持多品种策略：~~
    - ~~为 `MarketDataContext` 增加 `symbol` 字段~~
11. 考虑交易所差异性：
    - 增加 `exchange_type` 或 `exchange_specific` 字段
12. 增加使用文档和示例

---

## 📝 总结

基于**无状态策略**和**风控内部化**的设计原则，当前规范的核心架构是合理的：

### ✅ 当前设计的优点
- `StrategySpec` 服务的两个方法（`Health` 和 `Exec`）已经足够，无需增加生命周期或状态管理接口
- 无状态设计使策略易于测试、易于扩展、易于水平扩展
- 风控通过订单事件输出体现，避免了接口复杂化

### ⚠️ 需要改进的核心问题
1. **语法错误**（P0）：影响编译
2. **时间单位不统一**（P0）：影响数据正确性
3. **数据模型不完整**（P1）：缺少交易规则、订单详情、账户风控指标等关键信息
4. **错误处理不完善**（P1）：策略执行失败时无法返回详细错误信息
5. **文档缺失**（P2）：缺少使用示例和流程说明

### 🎯 建议
优先解决 **P0 和 P1** 的问题，确保基础功能完备和数据模型完整，然后进行小规模回测验证。**P2** 的扩展性问题可以根据实际业务需求逐步迭代。
