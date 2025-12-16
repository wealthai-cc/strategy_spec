# 策略开发规范

## 背景及目标

### 背景

策略开发规范定义了如何编写 Python 策略代码，参考 JoinQuant 平台的设计理念，提供简化的策略开发接口。通过生命周期函数和 Context 对象，让策略开发者可以专注于策略逻辑，无需了解底层 gRPC 接口细节。

### 目标

- **简化开发**：通过 Python 文件编写策略，无需实现 gRPC 服务
- **生命周期管理**：提供清晰的策略生命周期函数
- **统一接口**：通过 Context 对象提供统一的账户、行情、下单接口
- **环境一致性**：同一策略代码可在回测、仿真、实盘运行

## 使用场景/用户故事

### 场景 1：编写简单策略

**用户故事**：开发者想编写一个简单的移动平均策略，根据价格突破均线进行买卖。

**流程**：
1. 创建 Python 策略文件
2. 实现 `initialize` 函数设置初始参数
3. 实现 `handle_bar` 函数处理 K 线数据
4. 使用 `context.history` 获取历史数据
5. 使用 `context.order_buy` 或 `context.order_sell` 下单

### 场景 2：处理订单状态

**用户故事**：策略需要根据订单成交情况调整后续操作。

**流程**：
1. 实现 `on_order` 函数
2. 检查订单状态（成交、取消、拒绝）
3. 根据订单执行结果调整策略逻辑
4. 可能需要补单或调整仓位

### 场景 3：风控处理

**用户故事**：策略需要响应风控事件，采取减仓或平仓措施。

**流程**：
1. 实现 `on_risk_event` 函数
2. 检查风控事件类型和账户风险度
3. 采取相应的风控措施（减仓、平仓）

## 接口/数据结构定义

### 生命周期函数

策略文件应包含以下生命周期函数：

#### initialize(context)

**功能**：策略初始化函数，在策略首次加载时调用一次。

**参数**：
- `context`：Context 对象，提供账户、行情、下单等接口

**调用时机**：策略首次加载时调用一次

**示例**：
```python
def initialize(context):
    # 设置策略参数
    context.symbol = "BTCUSDT"
    context.ma_period = 20
    context.quantity = 0.1
    
    # 可以访问策略参数
    if "ma_period" in context.params:
        context.ma_period = int(context.params["ma_period"])
```

#### before_trading(context)

**功能**：交易前准备函数，在每个交易周期开始前调用（可选）。

**参数**：
- `context`：Context 对象

**调用时机**：交易周期开始前（如每天开盘前、每小时开始前）

**示例**：
```python
def before_trading(context):
    # 交易前准备
    # 可以检查账户状态、清理过期订单等
    pass
```

#### handle_bar(context, bar)

**功能**：处理新 K 线数据，当新的 Bar 数据到达时调用（可选）。

**参数**：
- `context`：Context 对象
- `bar`：最新的 Bar 对象，包含 OHLCV 数据

**调用时机**：当 `MARKET_DATA_TRIGGER_TYPE` 触发时

**示例**：
```python
def handle_bar(context, bar):
    # 获取历史数据
    ma = context.history(context.symbol, context.ma_period, "1h")
    
    # 策略逻辑
    if len(ma) >= context.ma_period:
        if bar.close > ma[-1]:
            # 价格突破均线，买入
            context.order_buy(context.symbol, context.quantity, price=bar.close)
        elif bar.close < ma[-1]:
            # 价格跌破均线，卖出
            context.order_sell(context.symbol, context.quantity, price=bar.close)
```

#### on_order(context, order)

**功能**：处理订单状态变更，当订单状态发生变化时调用（可选）。

**参数**：
- `context`：Context 对象
- `order`：订单对象，包含订单状态、成交信息等

**调用时机**：当 `ORDER_STATUS_TRIGGER_TYPE` 触发时

**示例**：
```python
def on_order(context, order):
    # 处理订单状态变更
    if order.status == "FILLED":
        print(f"订单成交: {order.order_id}, 成交价: {order.avg_fill_price}")
        # 可以根据成交情况调整策略
    elif order.status == "CANCELED":
        print(f"订单取消: {order.order_id}, 原因: {order.cancel_reason}")
    elif order.status == "REJECTED":
        print(f"订单拒绝: {order.order_id}")
```

#### on_risk_event(context, event)

**功能**：处理风控事件，当风控事件发生时调用（可选）。

**参数**：
- `context`：Context 对象
- `event`：风控事件对象，包含事件类型和详情

**调用时机**：当 `RISK_MANAGE_TRIGGER_TYPE` 触发时

**示例**：
```python
def on_risk_event(context, event):
    # 处理风控事件
    if event.risk_event_type == "MARGIN_CALL_EVENT_TYPE":
        # 需要补充保证金或减仓
        if context.account.risk_level > 80:
            # 风险度过高，减仓 50%
            for position in context.account.positions:
                if position.symbol == context.symbol:
                    reduce_qty = position.quantity * 0.5
                    context.order_sell(context.symbol, reduce_qty)
```

### Context 对象接口

Context 对象提供统一的接口访问账户、行情和下单功能：

#### 账户信息

- `context.account`：Account 对象，包含账户余额、持仓、风控指标等
- `context.portfolio`：Portfolio 对象，包含持仓信息和盈亏

#### 行情数据

- `context.current_bar`：当前最新的 Bar 对象
- `context.history(symbol, count, timeframe)`：获取历史 Bar 数据
  - `symbol`：交易对（如 "BTCUSDT"）
  - `count`：获取的 Bar 数量
  - `timeframe`：时间分辨率（如 "1h", "1d"）
  - 返回：Bar 对象列表，按时间顺序排列（最早的在前）

#### wealthdata 兼容模块（JoinQuant 兼容）

策略可以使用 `wealthdata` 模块进行数据访问，提供与 JoinQuant jqdatasdk 兼容的接口：

- `import wealthdata`：导入 wealthdata 模块（替代 `import jqdatasdk`）
- `wealthdata.get_price(symbol, count=None, end_date=None, frequency='1h', ...)`：获取价格数据
  - 返回：pandas DataFrame，包含 open, high, low, close, volume 列
  - 与 jqdatasdk.get_price() 接口完全一致
  - 内部映射到 `context.history()` 方法
- `wealthdata.get_bars(symbol, count=None, end_date=None, frequency='1h', ...)`：获取 K 线数据
  - 与 `get_price()` 功能相同，返回格式一致

**使用示例**：
```python
import wealthdata  # 替代 import jqdatasdk

def handle_bar(context, bar):
    # 使用 wealthdata.get_price() - JoinQuant 风格
    df = wealthdata.get_price(context.symbol, count=20, frequency='1h')
    ma = df['close'].mean()  # pandas DataFrame 操作
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)
```

**注意事项**：
- `wealthdata` 模块通过线程局部存储访问当前执行的 Context
- 数据范围受限于 ExecRequest 中的 market_data_context
- 返回 pandas DataFrame 格式，兼容现有 pandas 分析代码
- 支持零代码修改迁移（只需修改 import 语句）

#### 下单接口

- `context.order_buy(symbol, quantity, price=None)`：买入订单
  - `symbol`：交易对
  - `quantity`：数量
  - `price`：限价（可选，不提供则为市价单）
  - 返回：Order 对象

- `context.order_sell(symbol, quantity, price=None)`：卖出订单
  - 参数同上

- `context.cancel_order(order_id)`：撤销订单
  - `order_id`：订单 ID 或 unique_id
  - 返回：bool，是否成功

#### 策略参数

- `context.params`：字典，包含 ExecRequest.strategy_param 中的参数

## 约束与注意事项

### 生命周期函数要求

1. **initialize 必需**：`initialize` 函数是必需的，其他函数都是可选的
2. **函数签名**：函数签名必须与规范一致，参数类型和数量不能改变
3. **异常处理**：函数内部应处理异常，引擎会捕获未处理异常并返回错误
4. **执行时间**：函数应在 `ExecRequest.max_timeout` 秒内完成

### Context 对象使用

1. **只读访问**：Context 对象中的账户和行情数据是只读的，不应修改
2. **下单操作**：只能通过 Context 提供的下单方法进行，不能直接创建 Order 对象
3. **历史数据**：`history` 方法返回的数据来自 `ExecRequest.market_data_context`，数量受限于请求中的数据

### 策略文件格式

1. **Python 语法**：策略文件必须是有效的 Python 文件
2. **无特殊要求**：不需要继承特定类或实现特定接口
3. **模块化**：可以导入其他 Python 模块，但应避免复杂依赖

### 状态管理

1. **无状态原则**：策略函数应保持无状态，不依赖全局变量
2. **Context 存储**：可以在 `context` 对象上存储策略特定的数据（如 `context.symbol`）
3. **参数传递**：策略配置通过 `context.params` 传递

## 示例与用例

### 示例 1：简单移动平均策略

```python
def initialize(context):
    context.symbol = "BTCUSDT"
    context.ma_short = 5
    context.ma_long = 20
    context.quantity = 0.1

def handle_bar(context, bar):
    # 获取短期和长期均线
    ma_short = context.history(context.symbol, context.ma_short, "1h")
    ma_long = context.history(context.symbol, context.ma_long, "1h")
    
    if len(ma_short) < context.ma_short or len(ma_long) < context.ma_long:
        return  # 数据不足，跳过
    
    # 计算均线值（简化示例，实际需要计算 MA）
    short_ma_value = sum([b.close for b in ma_short[-context.ma_short:]]) / context.ma_short
    long_ma_value = sum([b.close for b in ma_long[-context.ma_long:]]) / context.ma_long
    
    # 金叉买入，死叉卖出
    if short_ma_value > long_ma_value:
        # 检查是否已有买单
        has_buy_order = any(
            o.direction_type == "BUY" and o.status in ["NEW", "PARTIALLY_FILLED"]
            for o in context.account.incomplete_orders
        )
        if not has_buy_order:
            context.order_buy(context.symbol, context.quantity)
    elif short_ma_value < long_ma_value:
        # 检查是否已有卖单
        has_sell_order = any(
            o.direction_type == "SELL" and o.status in ["NEW", "PARTIALLY_FILLED"]
            for o in context.account.incomplete_orders
        )
        if not has_sell_order:
            context.order_sell(context.symbol, context.quantity)
```

### 示例 2：带止损的策略

```python
def initialize(context):
    context.symbol = "BTCUSDT"
    context.quantity = 0.1
    context.stop_loss_pct = 0.02  # 2% 止损

def handle_bar(context, bar):
    # 策略逻辑
    # ...
    pass

def on_order(context, order):
    # 订单成交后设置止损
    if order.status == "FILLED" and order.direction_type == "BUY":
        # 买入成交，设置止损价
        stop_price = float(order.avg_fill_price.amount) * (1 - context.stop_loss_pct)
        context.order_sell(
            context.symbol, 
            order.executed_size, 
            price=stop_price
        )
```

### 示例 3：使用策略参数

```python
def initialize(context):
    # 从参数中读取配置
    context.symbol = context.params.get("symbol", "BTCUSDT")
    context.ma_period = int(context.params.get("ma_period", "20"))
    context.quantity = float(context.params.get("quantity", "0.1"))

def handle_bar(context, bar):
    # 使用配置的参数
    ma = context.history(context.symbol, context.ma_period, "1h")
    # 策略逻辑...
```

## Q&A、FAQ

### Q1：策略可以保存状态吗？

**A**：策略函数应保持无状态，但可以在 `context` 对象上存储策略特定的数据（如 `context.symbol`）。如果需要持久化状态，应由策略管理系统负责，通过 `strategy_param` 传递。

### Q2：如何获取历史数据？

**A**：使用 `context.history(symbol, count, timeframe)` 方法。数据来自 `ExecRequest.market_data_context`，数量受限于请求中提供的数据。

### Q3：如何下单？

**A**：使用 `context.order_buy()` 或 `context.order_sell()` 方法。可以指定限价（限价单）或不指定（市价单）。

### Q4：如何撤销订单？

**A**：使用 `context.cancel_order(order_id)` 方法，传入订单的 `order_id` 或 `unique_id`。

### Q5：策略可以访问外部服务吗？

**A**：不推荐。策略应避免网络 I/O 操作，以保证执行速度和稳定性。如需外部数据，应通过 `ExecRequest` 的 `market_data_context` 或其他字段传递。

### Q6：如何处理策略错误？

**A**：策略函数应捕获和处理异常。引擎会捕获未处理的异常，返回 `FAILED` 状态和错误信息。建议在关键操作处添加异常处理。

---

**相关文档**：
- [策略执行引擎规范](../strategy-engine/spec.md)
- [账户与持仓规范](../account/spec.md)
- [订单管理规范](../order/spec.md)
- [行情数据规范](../market-data/spec.md)

