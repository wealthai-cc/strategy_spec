# 订单管理规范

## 背景及目标

### 背景

订单是量化策略执行交易决策的载体，需要支持多种订单类型（市价、限价、止损等）和完整的订单生命周期管理。通过标准化的订单数据结构，确保策略能够准确创建、修改和撤销订单，并获取订单执行状态。

### 目标

- **多订单类型支持**：支持市价单、限价单、止损市价单、止损限价单
- **完整状态流转**：支持订单从新建到成交/取消/拒绝的完整生命周期
- **价格字段明确**：使用 `limit_price` 和 `stop_price` 明确区分限价和止损价
- **执行信息完整**：提供成交价格、成交数量、手续费等完整执行信息
- **幂等性保证**：通过 `unique_id` 确保订单的唯一性和幂等性

## 使用场景/用户故事

### 场景 1：创建限价买入订单

**用户故事**：策略判断当前价格低于目标价格，创建限价买入订单，等待价格回调时成交。

**流程**：
1. 策略构造 `Order` 对象
2. 设置 `order_type = LIMIT_ORDER_TYPE`
3. 设置 `limit_price` 为目标价格
4. 设置 `direction_type = BUY_DIRECTION_TYPE`
5. 通过 `OrderOpEvent` 创建订单

### 场景 2：止损平仓

**用户故事**：策略持有仓位，当价格跌破止损价时，触发止损市价单平仓。

**流程**：
1. 策略构造 `Order` 对象
2. 设置 `order_type = STOP_MARKET_ORDER_TYPE`
3. 设置 `stop_price` 为止损触发价
4. 设置 `direction_type = SELL_DIRECTION_TYPE`
5. 通过 `OrderOpEvent` 创建订单

### 场景 3：订单状态变更处理

**用户故事**：策略创建的订单已成交，系统触发 `ORDER_STATUS_TRIGGER_TYPE`，策略根据成交结果调整后续策略。

**流程**：
1. 系统检测到订单状态变更为 `FILLED_ORDER_STATUS_TYPE`
2. 系统构造 `ExecRequest`，设置 `ORDER_STATUS_TRIGGER_TYPE`
3. 在 `completed_orders[]` 中包含已成交订单
4. 策略读取订单执行信息（成交价格、数量、手续费等）
5. 策略根据执行结果调整后续交易决策

## 接口/数据结构定义

### 订单类型（OrderType）

```protobuf
enum OrderType {
    INVALID_ORDER_TYPE = 0;
    MARKET_ORDER_TYPE = 1;           // 市价单
    LIMIT_ORDER_TYPE = 2;            // 限价单
    STOP_MARKET_ORDER_TYPE = 3;      // 止损市价单
    STOP_LIMIT_ORDER_TYPE = 4;      // 止损限价单
}
```

### 订单状态（OrderStatusType）

```protobuf
enum OrderStatusType {
    INVALID_ORDER_STATUS_TYPE = 0;                    // 无效状态
    NEW_ORDER_STATUS_TYPE = 1;                        // 新建订单
    PARTIALLY_FILLED_ORDER_STATUS_TYPE = 2;           // 部分成交
    FILLED_ORDER_STATUS_TYPE = 3;                     // 完全成交
    CANCELED_ORDER_STATUS_TYPE = 4;                    // 已取消
    PENDING_CANCEL_ORDER_STATUS_TYPE = 5;             // 待取消中
    REJECTED_ORDER_STATUS_TYPE = 6;                    // 已拒绝
    EXPIRED_ORDER_STATUS_TYPE = 7;                     // 已过期
}
```

### 交易方向（DirectionType）

```protobuf
enum DirectionType {
    INVALID_DIRECTION_TYPE = 0;
    BUY_DIRECTION_TYPE = 1;          // 买入
    SELL_DIRECTION_TYPE = 2;         // 卖出
}
```

### 订单有效期（TimeInForceType）

```protobuf
enum TimeInForceType {
    INVALID_TIME_IN_FORCE_TYPE = 0;
    DAY_TIME_IN_FORCE_TYPE = 1;     // 当日有效（按市场所在时区计算"当日"）
    GTC_TIME_IN_FORCE_TYPE = 2;     // 撤单前有效
}
```

### 订单（Order）

```protobuf
message Order {
    string order_id = 1;                    // 交易所订单ID（仅当订单已经被交易所接纳时生效）
    int64 create_ts = 2;                    // 订单生成时间戳（unix毫秒时间戳）
    int64 update_ts = 3;                    // 订单更新时间戳（unix毫秒时间戳）
    string remark = 4;                      // 订单备注
    DirectionType direction_type = 5;       // 交易方向
    OrderType order_type = 6;               // 订单类型
    Currency limit_price = 7;               // limit价格（在OrderType含limit时）
    Currency stop_price = 8;                // 触发价（止损/止盈）
    string symbol = 9;                     // 品种
    double qty = 10;                        // 交易数量
    string unique_id = 11;                  // 订单唯一幂等ID（防重下单用）
    TimeInForceType time_in_force = 12;     // 订单有效时长（TIF）
    OrderStatusType status = 13;            // 订单状态
    double executed_size = 14;              // 已成交数量
    Currency avg_fill_price = 15;           // 平均成交金额
    Currency commission = 16;               // 已支付的佣金
    string cancel_reason = 17;              // 当订单已被取消时，被取消的原因
}
```

### 订单操作类型（OrderOpType）

```protobuf
enum OrderOpType {
    INVALID_ORDER_OP_TYPE = 0;
    CREATE_ORDER_OP_TYPE = 1;      // 创建新订单
    WITHDRAW_ORDER_OP_TYPE = 2;     // 撤销已有订单
    MODIFY_ORDER_OP_TYPE = 3;       // 修改已有订单
}
```

### 订单操作事件（OrderOpEvent）

```protobuf
message OrderOpEvent {
    OrderOpType order_op_type = 1;  // 订单操作事件类型
    Order order = 2;                // 订单
}
```

## 约束与注意事项

### 订单类型约束

1. **市价单**：`MARKET_ORDER_TYPE`
   - 不需要设置 `limit_price`
   - 以当前市场价格立即成交
   - 适用于需要快速成交的场景

2. **限价单**：`LIMIT_ORDER_TYPE`
   - 必须设置 `limit_price`
   - 只有当价格达到或优于限价时才会成交
   - 适用于希望控制成交价格的场景

3. **止损市价单**：`STOP_MARKET_ORDER_TYPE`
   - 必须设置 `stop_price`
   - 当价格触发止损价时，以市价成交
   - 适用于止损平仓场景

4. **止损限价单**：`STOP_LIMIT_ORDER_TYPE`
   - 必须设置 `stop_price` 和 `limit_price`
   - 当价格触发止损价时，转为限价单
   - 适用于需要控制止损成交价格的场景

### 价格字段使用

1. **limit_price**：限价单的价格，或止损限价单的限价
   - 买入限价单：`limit_price` 为最高买入价
   - 卖出限价单：`limit_price` 为最低卖出价

2. **stop_price**：止损/止盈触发价
   - 买入止损单：当价格 >= `stop_price` 时触发
   - 卖出止损单：当价格 <= `stop_price` 时触发

3. **价格精度**：价格必须符合交易所的精度要求（通过 `get_trading_rule` 查询）

### 订单状态流转

**正常流转**：
```
NEW → PARTIALLY_FILLED → FILLED
NEW → CANCELED
NEW → REJECTED
NEW → EXPIRED
```

**撤销中状态**：
```
NEW → PENDING_CANCEL → CANCELED
PARTIALLY_FILLED → PENDING_CANCEL → CANCELED
```

### 幂等性保证

1. **unique_id**：每个订单必须设置唯一的 `unique_id`
   - 建议格式：`{exec_id}_{timestamp}_{sequence}`
   - 系统使用 `unique_id` 进行去重检查

2. **重复提交**：如果使用相同的 `unique_id` 重复提交订单，系统会返回已存在的订单

### 数量与精度

1. **数量精度**：`qty` 必须符合交易所的精度要求
   - 通过 `get_trading_rule` 查询 `quantity_step` 和 `quantity_precision`
   - 数量必须是 `quantity_step` 的整数倍

2. **最小数量**：`qty` 必须 >= `min_quantity`（通过 `get_trading_rule` 查询）

### 订单有效期

1. **当日有效**：`DAY_TIME_IN_FORCE_TYPE`
   - 订单在当日交易时间结束时自动取消
   - "当日"按交易所所在时区计算

2. **撤单前有效**：`GTC_TIME_IN_FORCE_TYPE`
   - 订单一直有效，直到被手动撤销或成交
   - 适用于长期挂单场景

## 示例与用例

### 示例 1：创建限价买入订单

```python
# 构造订单对象
order = Order()
order.unique_id = f"{exec_id}_{int(time.time() * 1000)}_001"
order.symbol = "BTCUSDT"
order.direction_type = DirectionType.BUY_DIRECTION_TYPE
order.order_type = OrderType.LIMIT_ORDER_TYPE
order.limit_price.currency_type = CurrencyType.USDT_CURRENCY_TYPE
order.limit_price.amount = 42000.0
order.qty = 0.1
order.time_in_force = TimeInForceType.GTC_TIME_IN_FORCE_TYPE
order.remark = "策略买入信号"

# 创建订单操作事件
order_op_event = OrderOpEvent()
order_op_event.order_op_type = OrderOpType.CREATE_ORDER_OP_TYPE
order_op_event.order = order

# 添加到响应
exec_response.order_op_event.append(order_op_event)
```

### 示例 2：创建止损市价单

```python
# 构造止损订单
order = Order()
order.unique_id = f"{exec_id}_{int(time.time() * 1000)}_002"
order.symbol = "BTCUSDT"
order.direction_type = DirectionType.SELL_DIRECTION_TYPE
order.order_type = OrderType.STOP_MARKET_ORDER_TYPE
order.stop_price.currency_type = CurrencyType.USDT_CURRENCY_TYPE
order.stop_price.amount = 40000.0  # 止损触发价
order.qty = 0.1
order.remark = "止损平仓"

# 创建订单操作事件
order_op_event = OrderOpEvent()
order_op_event.order_op_type = OrderOpType.CREATE_ORDER_OP_TYPE
order_op_event.order = order

exec_response.order_op_event.append(order_op_event)
```

### 示例 3：撤销订单

```python
# 从 incomplete_orders 中找到要撤销的订单
target_order = None
for order in exec_request.incomplete_orders:
    if order.unique_id == "target_unique_id":
        target_order = order
        break

if target_order:
    # 创建撤销操作事件
    order_op_event = OrderOpEvent()
    order_op_event.order_op_type = OrderOpType.WITHDRAW_ORDER_OP_TYPE
    order_op_event.order = target_order
    exec_response.order_op_event.append(order_op_event)
```

### 示例 4：处理订单成交

```python
# 从 completed_orders 中查找已成交订单
for order in exec_request.completed_orders:
    if order.status == OrderStatusType.FILLED_ORDER_STATUS_TYPE:
        print(f"订单 {order.unique_id} 已成交")
        print(f"成交数量: {order.executed_size}")
        print(f"平均成交价: {order.avg_fill_price.amount}")
        print(f"手续费: {order.commission.amount}")
        
        # 根据成交结果调整策略
        if order.direction_type == DirectionType.BUY_DIRECTION_TYPE:
            # 买入成交，可能需要调整止损价
            pass
```

### 示例 5：数量精度调整

```python
# 获取交易规则
trading_rule = get_trading_rule("binance", "BTCUSDT")
min_quantity = trading_rule["min_quantity"]
quantity_step = trading_rule["quantity_step"]
quantity_precision = trading_rule["quantity_precision"]

# 计算目标数量
target_qty = 0.123456789

# 调整数量
target_qty = max(target_qty, min_quantity)  # 不小于最小数量
target_qty = round(target_qty / quantity_step) * quantity_step  # 符合步进
target_qty = round(target_qty, quantity_precision)  # 符合精度

order.qty = target_qty
```

## Q&A、FAQ

### Q1：如何区分 limit_price 和 stop_price？

**A**：
- `limit_price`：限价单的成交价格，或止损限价单的限价
- `stop_price`：止损/止盈的触发价格
- 对于普通限价单，只设置 `limit_price`
- 对于止损单，必须设置 `stop_price`，如果是止损限价单，还需要设置 `limit_price`

### Q2：订单被拒绝的原因？

**A**：订单可能被拒绝的原因包括：
- 数量不符合交易所要求（小于最小数量、不符合步进等）
- 价格不符合交易所要求（精度错误、超出价格范围等）
- 账户余额不足
- 风控限制（杠杆超限、持仓超限等）
- 交易所系统错误

被拒绝的订单状态为 `REJECTED_ORDER_STATUS_TYPE`，可以通过日志或错误信息查看具体原因。

### Q3：如何修改订单？

**A**：使用 `MODIFY_ORDER_OP_TYPE` 操作类型，在 `Order` 对象中设置新的价格或数量。注意：
- 只能修改未成交的订单（状态为 `NEW` 或 `PARTIALLY_FILLED`）
- 修改后的价格和数量必须符合交易所要求
- 某些交易所可能不支持修改订单，需要先撤销再创建

### Q4：部分成交订单如何处理？

**A**：部分成交的订单状态为 `PARTIALLY_FILLED_ORDER_STATUS_TYPE`：
- `executed_size` 表示已成交数量
- `qty - executed_size` 表示剩余未成交数量
- 可以继续等待成交，也可以撤销剩余部分

### Q5：订单的唯一性如何保证？

**A**：通过 `unique_id` 字段保证订单的唯一性：
- 每个订单必须设置唯一的 `unique_id`
- 建议使用 `{exec_id}_{timestamp}_{sequence}` 格式
- 系统会检查 `unique_id` 的重复，重复的订单会被拒绝或返回已存在的订单

---

**相关文档**：
- [策略执行引擎规范](./spec_strategy_engine.md)
- [账户与持仓规范](./spec_account.md)
- [Python SDK 规范](./spec_python_sdk.md)

