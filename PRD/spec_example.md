# OpenSpec 示例文档 - 策略下单接口

> 本文档以"策略下单接口"为例，展示完整的 OpenSpec 结构，作为其他规格文档的参考模板。

## 背景及目标

### 背景

策略下单接口是量化策略执行交易决策的核心功能，需要支持多种订单类型、参数校验、成本计算等复杂场景。通过标准化的下单接口，确保策略能够准确、高效地创建订单。

### 目标

- **多订单类型支持**：支持市价单、限价单、止损单等多种订单类型
- **参数自动校验**：自动校验数量、价格等参数是否符合交易所要求
- **成本透明化**：提供佣金计算，帮助策略评估交易成本
- **错误处理完善**：提供明确的错误信息和处理建议

## 使用场景/用户故事

### 场景 1：限价买入订单

**用户故事**：策略判断当前价格低于目标价格，希望以限价单买入，等待价格回调时成交。

**作为策略开发者**，我希望能够：
- 指定目标价格和数量
- 系统自动校验参数合法性
- 订单创建成功后返回订单信息

**验收标准**：
- 订单参数符合交易所要求（数量、价格精度等）
- 订单成功创建并返回订单 ID
- 如果参数不合法，返回明确的错误信息

### 场景 2：止损平仓

**用户故事**：策略持有仓位，当价格跌破止损价时，触发止损市价单平仓。

**作为策略开发者**，我希望能够：
- 设置止损触发价格
- 系统在价格触发时自动以市价平仓
- 获取平仓执行结果

**验收标准**：
- 止损价格设置成功
- 价格触发时订单自动执行
- 平仓结果准确记录

### 场景 3：订单参数自动调整

**用户故事**：策略计算的目标数量可能不符合交易所要求，系统应自动调整。

**作为策略开发者**，我希望能够：
- 输入目标数量（可能不符合交易所要求）
- 系统自动调整到符合要求的值
- 返回调整后的数量

**验收标准**：
- 数量自动调整为最小数量的整数倍
- 价格精度自动调整
- 调整后的参数符合交易所要求

## 接口/数据结构定义

### 下单接口

```python
def create_order(
    broker: str,
    symbol: str,
    direction: DirectionType,
    order_type: OrderType,
    quantity: float,
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    time_in_force: TimeInForceType = TimeInForceType.GTC_TIME_IN_FORCE_TYPE
) -> Order
```

**参数说明**：
- `broker`：交易所标识（如 "binance"）
- `symbol`：交易品种（如 "BTCUSDT"）
- `direction`：交易方向（买入/卖出）
- `order_type`：订单类型（市价/限价/止损）
- `quantity`：交易数量
- `limit_price`：限价（限价单和止损限价单需要）
- `stop_price`：止损触发价（止损单需要）
- `time_in_force`：订单有效期

**返回值**：
- `Order`：创建的订单对象，包含订单 ID、状态等信息

**异常**：
- `InvalidParameterError`：参数不合法（数量、价格不符合要求）
- `InsufficientBalanceError`：账户余额不足
- `ExchangeError`：交易所错误（网络错误、系统错误等）

### 参数校验接口

```python
def validate_order_params(
    broker: str,
    symbol: str,
    quantity: float,
    price: Optional[float] = None
) -> ValidationResult
```

**返回值**：
```python
class ValidationResult:
    is_valid: bool           # 是否通过校验
    errors: List[str]        # 错误信息列表
    adjusted_quantity: float # 调整后的数量
    adjusted_price: float    # 调整后的价格
```

## 约束与注意事项

### 参数约束

1. **数量约束**：
   - 必须 >= 最小下单量（通过 `get_trading_rule` 查询）
   - 必须是数量步进的整数倍
   - 必须符合数量精度要求

2. **价格约束**：
   - 限价单必须提供 `limit_price`
   - 止损单必须提供 `stop_price`
   - 价格必须符合价格精度和价格步进要求

3. **余额约束**：
   - 买入订单需要足够的可用余额
   - 卖出订单需要足够的持仓数量

### 订单类型约束

1. **市价单**：
   - 不需要 `limit_price`
   - 立即以市场价格成交
   - 可能产生滑点

2. **限价单**：
   - 必须提供 `limit_price`
   - 只有当价格达到或优于限价时才会成交
   - 可能不会立即成交

3. **止损单**：
   - 必须提供 `stop_price`
   - 当价格触发止损价时执行
   - 止损市价单以市价成交，止损限价单需要额外提供 `limit_price`

### 错误处理

1. **参数错误**：返回 `InvalidParameterError`，包含详细的错误信息
2. **余额不足**：返回 `InsufficientBalanceError`，说明缺少的金额或数量
3. **交易所错误**：返回 `ExchangeError`，包含交易所返回的错误信息

## 示例与用例

### 示例 1：创建限价买入订单

```python
from wealthai_sdk import create_order, DirectionType, OrderType, TimeInForceType

try:
    order = create_order(
        broker="binance",
        symbol="BTCUSDT",
        direction=DirectionType.BUY_DIRECTION_TYPE,
        order_type=OrderType.LIMIT_ORDER_TYPE,
        quantity=0.1,
        limit_price=42000.0,
        time_in_force=TimeInForceType.GTC_TIME_IN_FORCE_TYPE
    )
    
    print(f"订单创建成功: {order.order_id}")
    print(f"订单状态: {order.status}")
    
except InvalidParameterError as e:
    print(f"参数错误: {e}")
except InsufficientBalanceError as e:
    print(f"余额不足: {e}")
except ExchangeError as e:
    print(f"交易所错误: {e}")
```

### 示例 2：创建止损市价单

```python
try:
    order = create_order(
        broker="binance",
        symbol="BTCUSDT",
        direction=DirectionType.SELL_DIRECTION_TYPE,
        order_type=OrderType.STOP_MARKET_ORDER_TYPE,
        quantity=0.1,
        stop_price=40000.0  # 止损触发价
    )
    
    print(f"止损单创建成功: {order.order_id}")
    
except Exception as e:
    print(f"创建失败: {e}")
```

### 示例 3：参数自动调整

```python
from wealthai_sdk import validate_order_params, create_order

# 先校验参数
validation = validate_order_params(
    broker="binance",
    symbol="BTCUSDT",
    quantity=0.123456789,  # 可能不符合要求
    price=42000.123456789  # 可能不符合精度要求
)

if not validation.is_valid:
    print(f"参数校验失败: {validation.errors}")
    print(f"建议使用调整后的参数:")
    print(f"  数量: {validation.adjusted_quantity}")
    print(f"  价格: {validation.adjusted_price}")

# 使用调整后的参数创建订单
order = create_order(
    broker="binance",
    symbol="BTCUSDT",
    direction=DirectionType.BUY_DIRECTION_TYPE,
    order_type=OrderType.LIMIT_ORDER_TYPE,
    quantity=validation.adjusted_quantity,
    limit_price=validation.adjusted_price
)
```

### 示例 4：完整的下单流程

```python
def place_order_with_validation(
    broker: str,
    symbol: str,
    direction: DirectionType,
    order_type: OrderType,
    target_quantity: float,
    target_price: Optional[float] = None
) -> Order:
    """带参数校验的下单流程"""
    
    # 1. 校验参数
    validation = validate_order_params(
        broker=broker,
        symbol=symbol,
        quantity=target_quantity,
        price=target_price
    )
    
    if not validation.is_valid:
        raise ValueError(f"参数校验失败: {validation.errors}")
    
    # 2. 创建订单
    order = create_order(
        broker=broker,
        symbol=symbol,
        direction=direction,
        order_type=order_type,
        quantity=validation.adjusted_quantity,
        limit_price=validation.adjusted_price if order_type == OrderType.LIMIT_ORDER_TYPE else None
    )
    
    return order

# 使用示例
try:
    order = place_order_with_validation(
        broker="binance",
        symbol="BTCUSDT",
        direction=DirectionType.BUY_DIRECTION_TYPE,
        order_type=OrderType.LIMIT_ORDER_TYPE,
        target_quantity=0.1,
        target_price=42000.0
    )
    print(f"订单创建成功: {order.order_id}")
except Exception as e:
    print(f"下单失败: {e}")
```

## Q&A、FAQ

### Q1：如何选择订单类型？

**A**：
- **市价单**：需要立即成交，不关心成交价格
- **限价单**：希望控制成交价格，可以等待
- **止损单**：需要设置止损或止盈

### Q2：参数校验失败怎么办？

**A**：使用 `validate_order_params` 接口获取调整后的参数，或根据错误信息手动调整参数。

### Q3：如何计算交易成本？

**A**：使用 `get_commission_rates` 接口获取佣金费率，根据订单类型（Maker/Taker）计算成本。

### Q4：订单创建后如何查询状态？

**A**：订单创建后返回的 `Order` 对象包含 `order_id`，可以通过订单查询接口获取最新状态。

### Q5：如何撤销订单？

**A**：使用订单撤销接口，传入订单 ID 或 `unique_id` 即可撤销。

---

**相关文档**：
- [订单管理规范](./spec_order.md)
- [Python SDK 规范](./spec_python_sdk.md)
- [策略执行引擎规范](./spec_strategy_engine.md)

---

**备注**：本文档为 OpenSpec 结构示例，实际的下单接口实现可能有所不同，请参考具体的接口文档。

