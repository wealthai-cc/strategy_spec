# 策略执行引擎规范

## 背景及目标

### 背景

策略执行引擎是 WealthAI 量化策略系统的核心组件，负责在策略与策略管理系统之间提供标准化的交互接口。通过定义统一的 Proto3 接口规范，实现策略的无状态执行、多环境复用（回测、仿真、真实交易）以及跨语言支持。

策略执行引擎框架（类似 JoinQuant）作为 StrategySpec 接口的实现层，将 Python 策略文件转换为 gRPC 调用，简化策略开发流程。

### 目标

- **无状态设计**：策略不保存内部状态，每次执行为纯函数式调用
- **标准化接口**：通过 gRPC 服务提供统一的策略执行接口
- **多触发支持**：支持行情数据、风控事件、订单状态变更等多种触发机制
- **幂等保证**：通过执行 ID 确保同一触发事件的重复执行可去重
- **并发安全**：同一账户的同一策略由系统保证串行执行
- **简化开发**：通过策略执行引擎框架，支持 Python 策略文件开发，无需直接实现 gRPC 服务

## 使用场景/用户故事

### 场景 1：行情驱动策略执行

**用户故事**：当新的 K 线数据到达时，系统自动触发策略执行，策略根据当前行情和账户状态做出交易决策。

**流程**：
1. 市场数据服务推送新的 Bar 数据
2. 系统构造 `ExecRequest`，设置 `MARKET_DATA_TRIGGER_TYPE`
3. 调用策略的 `Exec` 接口
4. 策略返回订单操作事件（如创建买入订单）
5. 系统处理订单操作事件

### 场景 2：风控事件触发

**用户故事**：当账户风险度达到阈值时，系统触发策略执行，策略可以采取减仓、平仓等风控措施。

**流程**：
1. 风控系统检测到账户风险度超标
2. 系统构造 `ExecRequest`，设置 `RISK_MANAGE_TRIGGER_TYPE`
3. 调用策略的 `Exec` 接口，传递风控事件详情
4. 策略返回风控订单操作（如强制平仓）

### 场景 3：订单状态变更触发

**用户故事**：当订单成交或撤销时，触发策略执行，策略可以根据订单执行结果调整后续策略。

**流程**：
1. 订单系统检测到订单状态变更（成交/撤销/拒绝）
2. 系统构造 `ExecRequest`，设置 `ORDER_STATUS_TRIGGER_TYPE`
3. 调用策略的 `Exec` 接口，传递订单状态信息
4. 策略返回后续订单操作（如补单、调整仓位）

## 接口/数据结构定义

### 服务接口

```protobuf
service StrategySpec {
    // Health 策略健康探测接口
    rpc Health(google.protobuf.Empty) returns (HealthResponse);
    
    // Exec 策略执行接口，只支持执行单品种下的同步策略
    rpc Exec(ExecRequest) returns (ExecResponse);
}
```

### 健康检查接口

**HealthResponse**：
- `status`：健康状态枚举
  - `HEALTHY`：健康
  - `DEGRADED`：降级（部分功能不可用）
  - `UNHEALTHY`：不健康
- `message`：状态描述
- `details[]`：详细信息（不可用依赖、降级原因等）

### 执行请求（ExecRequest）

**核心字段**：
- `max_timeout`：最大超时秒数
- `trigger_type`：触发类型枚举
  - `MARKET_DATA_TRIGGER_TYPE`：行情数据触发
  - `RISK_MANAGE_TRIGGER_TYPE`：风控触发
  - `ORDER_STATUS_TRIGGER_TYPE`：订单状态变更触发
- `trigger_detail`：触发详情（根据 trigger_type 填充对应字段）
- `market_data_context[]`：市场行情上下文数据，支持多分辨率行情数据同时传递
- `account`：当前账户数据（含风控指标）
- `incomplete_orders[]`：所有未完成订单
- `completed_orders[]`：所有已完成订单（时间范围在策略管理系统配置）
- `exchange`：交易所名称（用于佣金计算等）
  - 支持扩展的交易所标识，使用小写字符串（如 "binance", "okx", "bybit"）
  - 仅支持字母数字和连字符
  - 默认为 "binance"（向后兼容）
  - 框架主要支持 Binance，同时保持可扩展性，可通过适配器模式添加其他交易所
- `exec_id`：执行唯一 ID（用于幂等性保证）
- `strategy_param`：透传给策略的参数（map<string,string>）

### 执行响应（ExecResponse）

**核心字段**：
- `order_op_event[]`：订单操作事件列表
  - `order_op_type`：操作类型（创建/撤销/修改）
  - `order`：订单对象
- `status`：执行状态枚举
  - `SUCCESS`：执行成功
  - `PARTIAL_SUCCESS`：部分成功（部分订单生成或校验失败）
  - `FAILED`：执行失败
- `error_message`：错误信息（当 status=FAILED 时）
- `warnings[]`：警告信息（非致命问题）

### 触发详情（TriggerDetail）

**MarketDataTriggerDetail**（行情触发）：
- `server_ts`：服务器 Unix 时间戳（毫秒）

**RiskManageTriggerDetail**（风控触发）：
- `risk_event_type`：风控事件类型
  - `MARGIN_CALL_EVENT_TYPE`：补齐保证金风控
- `remark`：备注信息

**OrderStatusTriggerDetail**（订单状态触发）：
- 当前 proto 文件中未定义该字段（`TriggerDetail` 仅包含 `market_data_trigger_detail` 和 `risk_manage_trigger_detail`）
- 订单状态信息通过 `ExecRequest.completed_orders` 或 `incomplete_orders` 传递
- 触发该类型的订单可通过订单状态变更识别（如从 `NEW` 变为 `FILLED`、`CANCELED` 等）
- 当使用 `ORDER_STATUS_TRIGGER_TYPE` 时，`trigger_detail` 可以为空，订单信息从 `completed_orders` 或 `incomplete_orders` 中获取
- 未来版本可能增加 `order_status_trigger_detail` 字段，包含 `triggered_order_id` 等信息（参考 `review.md` 中的改进建议）

## 约束与注意事项

### 并发与幂等约定

1. **串行执行**：同一账户的同一策略由系统保证串行执行，避免并发冲突
2. **幂等性**：系统对同一触发事件的重复执行进行去重；`ExecRequest.exec_id` 作为执行幂等 ID
3. **超时控制**：策略必须在 `max_timeout` 秒内返回响应，超时将被系统取消

### 无状态要求

1. **纯函数式**：策略的 `Exec` 方法应为纯函数，不依赖外部状态
2. **状态透传**：所有必要的状态信息通过 `ExecRequest` 传递（账户、订单、行情等）
3. **参数配置**：策略配置通过 `strategy_param` 透传，不保存在策略内部

### 错误处理

1. **错误响应**：策略执行失败时，必须返回 `FAILED` 状态和详细的 `error_message`
2. **部分成功**：当部分订单操作成功、部分失败时，返回 `PARTIAL_SUCCESS` 并在 `warnings` 中说明
3. **异常捕获**：策略应捕获所有异常，避免未处理异常导致系统崩溃

### 性能要求

1. **响应时间**：策略执行应在毫秒级完成，避免阻塞系统
2. **资源限制**：策略不应进行长时间计算或阻塞 I/O 操作
3. **内存管理**：策略应避免内存泄漏，及时释放资源

## 示例与用例

### 示例 1：行情触发买入订单

**请求**：
```json
{
  "max_timeout": 5,
  "trigger_type": "MARKET_DATA_TRIGGER_TYPE",
  "trigger_detail": {
    "market_data_trigger_detail": {
      "server_ts": 1704067200000
    }
  },
  "market_data_context": [{
    "symbol": "BTCUSDT",
    "timeframe": "1m",
    "bars": [{
      "open_time": 1704067140000,
      "close_time": 1704067200000,
      "open": "42000.00",
      "high": "42100.00",
      "low": "41900.00",
      "close": "42050.00",
      "volume": "100.5"
    }]
  }],
  "account": {
    "account_id": "acc_001",
    "total_net_value": {
      "currency_type": "USDT_CURRENCY_TYPE",
      "amount": 10000.0
    },
    "available_margin": {
      "currency_type": "USDT_CURRENCY_TYPE",
      "amount": 5000.0
    }
  },
  "exchange": "binance",
  "exec_id": "exec_20240101_001"
}
```

**响应**：
```json
{
  "order_op_event": [{
    "order_op_type": "CREATE_ORDER_OP_TYPE",
    "order": {
      "unique_id": "order_001",
      "symbol": "BTCUSDT",
      "direction_type": "BUY_DIRECTION_TYPE",
      "order_type": "LIMIT_ORDER_TYPE",
      "limit_price": {
        "currency_type": "USDT_CURRENCY_TYPE",
        "amount": 42000.0
      },
      "qty": 0.1,
      "time_in_force": "GTC_TIME_IN_FORCE_TYPE"
    }
  }],
  "status": "SUCCESS"
}
```

### 示例 2：风控触发强制平仓

**请求**：
```json
{
  "trigger_type": "RISK_MANAGE_TRIGGER_TYPE",
  "trigger_detail": {
    "risk_manage_trigger_detail": {
      "risk_event_type": "MARGIN_CALL_EVENT_TYPE",
      "remark": "账户风险度达到 90%，需要补充保证金或减仓"
    }
  },
  "account": {
    "account_id": "acc_001",
    "risk_level": 90.0,
    "margin_ratio": 0.85
  },
  "positions": [{
    "symbol": "BTCUSDT",
    "position_side": "LONG_POSITION_SIDE",
    "quantity": 1.0
  }],
  "exec_id": "exec_20240101_002"
}
```

**响应**：
```json
{
  "order_op_event": [{
    "order_op_type": "CREATE_ORDER_OP_TYPE",
    "order": {
      "unique_id": "order_002",
      "symbol": "BTCUSDT",
      "direction_type": "SELL_DIRECTION_TYPE",
      "order_type": "MARKET_ORDER_TYPE",
      "qty": 0.5
    }
  }],
  "status": "SUCCESS",
  "warnings": ["已减仓 50% 以降低风险度"]
}
```

## Q&A、FAQ

### Q1：策略可以保存状态吗？

**A**：不可以。策略必须是无状态的，所有状态信息通过 `ExecRequest` 传递。如果需要保存策略状态，应由策略管理系统负责持久化，并在下次执行时通过 `strategy_param` 或其他字段传递。

### Q2：如何处理策略执行超时？

**A**：策略应在 `max_timeout` 秒内返回响应。如果策略执行时间较长，建议：
1. 优化策略逻辑，减少计算时间
2. 将复杂计算拆分为多个步骤，通过多次触发完成
3. 在策略内部设置超时检查，超时前返回部分结果

### Q3：多个订单操作事件的处理顺序？

**A**：`order_op_event[]` 中的事件按顺序处理。策略应确保事件顺序符合业务逻辑（如先撤销旧订单，再创建新订单）。

### Q4：如何保证订单的唯一性？

**A**：每个订单必须设置唯一的 `unique_id`，系统使用该 ID 进行幂等性检查。建议使用 `exec_id + 序号` 或 UUID 生成。

### Q5：策略可以访问外部服务吗？

**A**：不推荐。策略应避免网络 I/O 操作，以保证执行速度和稳定性。如需外部数据，应通过 `ExecRequest` 的 `market_data_context` 或其他字段传递。

---

## 策略执行引擎架构

### 架构概述

策略执行引擎框架作为 StrategySpec 接口的实现层，将 Python 策略文件转换为 gRPC 调用。引擎负责：

1. **策略加载**：加载 Python 策略文件，验证生命周期函数，设置 `wealthdata` 模块
2. **事件调度**：将 ExecRequest 触发类型映射到策略生命周期函数
3. **Context 管理**：从 ExecRequest 构建 Context 对象，管理线程局部存储
4. **订单收集**：收集策略函数中的订单操作，转换为 ExecResponse

### 架构层次

```
策略管理系统
    ↓ (gRPC 调用)
StrategySpec.Exec(ExecRequest)
    ↓
策略执行引擎（Engine）
    ├── 策略加载器（Strategy Loader）
    ├── 事件调度器（Event Dispatcher）
    ├── Context 管理器（Context Manager）
    └── 生命周期管理器（Lifecycle Manager）
    ↓
Python 策略文件
    ├── initialize(context)
    ├── before_trading(context)
    ├── handle_bar(context, bar)
    ├── on_order(context, order)
    └── on_risk_event(context, event)
```

### 事件到函数映射

引擎将 ExecRequest 的触发类型映射到策略生命周期函数：

- `MARKET_DATA_TRIGGER_TYPE` → `handle_bar(context, bar)`
- `ORDER_STATUS_TRIGGER_TYPE` → `on_order(context, order)`
- `RISK_MANAGE_TRIGGER_TYPE` → `on_risk_event(context, event)`

### 执行流程

1. **接收 ExecRequest**：引擎接收来自策略管理系统的 ExecRequest
2. **加载策略**：根据策略标识加载对应的 Python 策略文件
3. **构建 Context**：从 ExecRequest 中提取数据，构建 Context 对象
4. **设置 wealthdata 模块**：在策略加载前设置策略特定的 `g` 和 `log` 对象到 `wealthdata` 模块
5. **设置线程局部存储**：将 Context 和策略模块设置到线程局部存储，供 wealthdata 模块访问
6. **事件调度**：根据 trigger_type 调用对应的生命周期函数
7. **收集订单**：收集策略函数中的订单操作（通过 Context 的下单方法）
8. **清理线程局部存储**：执行完成后清理 Context 和策略模块引用（使用 finally 确保清理）
9. **返回响应**：将订单操作转换为 ExecResponse 返回

### wealthdata 模块设置和策略加载

引擎 SHALL 在加载策略文件时设置 `wealthdata` 模块，确保所有 JoinQuant 兼容的 API 都可用。

**所有 JoinQuant 兼容的 API SHALL 在 `wealthdata` 模块中定义，引擎只负责设置策略特定的实例（g, log），不进行模块注入。**

- **策略加载前设置 wealthdata 模块**：
  - **WHEN** 引擎开始加载策略文件
  - **THEN** 引擎 SHALL 在策略加载之前设置 `wealthdata` 模块：
    - 创建策略特定的 `g` 对象并设置到 `wealthdata.g`
    - 创建策略特定的 `log` 对象并设置到 `wealthdata.log`
    - 设置策略模块到线程局部存储（用于 `run_daily`, `set_benchmark` 等）

- **策略导入 wealthdata**：
  - **WHEN** 策略文件执行 `from wealthdata import *`
  - **THEN** 策略 SHALL 能够访问所有 JoinQuant 兼容的 API
  - **AND** 所有函数和对象都来自 `wealthdata` 模块，无需运行时注入

- **策略模块引用更新**：
  - **WHEN** 策略文件加载完成
  - **THEN** 引擎 SHALL 更新策略模块中的 `log` 和 `g` 引用，确保它们指向 `wealthdata` 模块中的最新实例
  - **AND** 这确保即使策略在导入时获取了引用，也能使用正确的实例

- **无模块注入**：
  - **WHEN** 引擎加载策略
  - **THEN** 引擎 SHALL NOT 将函数注入到策略模块的命名空间
  - **AND** 所有函数和对象都通过 `wealthdata` 模块提供
  - **AND** 策略必须使用 `from wealthdata import *` 来访问这些功能

### Context 线程局部存储

引擎 SHALL 管理 Context 对象在线程局部存储中的生命周期，以支持 wealthdata 兼容模块：

- **设置 Context**：在执行策略函数前，引擎 SHALL 将 Context 设置到线程局部存储
- **清理 Context**：在执行完成后（成功或失败），引擎 SHALL 清理线程局部存储中的 Context
- **线程安全**：每个执行线程 SHALL 有独立的 Context，支持并发策略执行
- **异常处理**：即使策略执行抛出异常，引擎 SHALL 确保 Context 被正确清理
- **策略模块清理**：在执行完成后，引擎 SHALL 清理线程局部存储中的策略模块引用

- **Context 设置和清理**：
  - **WHEN** 引擎开始执行策略函数
  - **THEN** 引擎 SHALL 在执行前将 Context 设置到线程局部存储
  - **AND** 在执行完成后（成功或失败），引擎 SHALL 清理线程局部存储中的 Context
  - **AND** 引擎 SHALL 清理线程局部存储中的策略模块引用

- **异常情况下的清理**：
  - **WHEN** 策略执行抛出异常
  - **THEN** 引擎 SHALL 确保 Context 被正确清理（使用 finally 块）
  - **AND** 引擎 SHALL 确保策略模块引用被正确清理

### 与现有接口的关系

- StrategySpec.Exec 接口保持不变
- 引擎作为策略实现，将 Python 策略转换为 Exec 调用
- 引擎内部处理事件调度和生命周期管理
- 策略开发者无需直接实现 gRPC 服务
- 支持两种策略实现方式：
  - Python 策略文件（通过引擎执行）
  - 直接实现 gRPC 服务（高级用法）

**相关文档**：
- [策略开发规范](../strategy-development/spec.md) - Python 策略文件开发指南
- [账户与持仓规范](../account/spec.md)
- [订单管理规范](../order/spec.md)
- [行情数据规范](../market-data/spec.md)

