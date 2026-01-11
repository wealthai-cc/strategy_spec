# Strategy Specification (策略规范)

本模块定义了量化交易策略开发的标准接口、基类以及相关的数据结构。所有的用户策略都必须基于此规范进行开发。

## 1. Strategy 基类

`strategy_spec.strategy.Strategy` 是所有策略的基类。它定义了策略的生命周期和事件处理接口。

### 生命周期方法

*   `on_init(self, context: Context)`: 策略初始化时调用。用于加载配置、初始化变量等。
*   `on_start(self, context: Context)`: 策略启动时调用。
*   `on_stop(self, context: Context)`: 策略停止时调用。

### 事件处理方法

策略通过重写以下方法来处理市场事件：

*   `on_bar(self, context: Context, bar: Bar)`: 当新的 K 线 (Bar) 数据到达时触发。
*   `on_tick(self, context: Context, tick: Tick)`: 当新的 Tick (逐笔行情) 数据到达时触发。
*   `on_order_status(self, context: Context, order: Order)`: 当订单状态发生变化（如成交、撤单）时触发。
*   `on_timer(self, context: Context)`: 定时器触发（如果引擎配置了定时任务）。

### 交易操作

策略类提供了简化的交易接口：

*   `buy(context, symbol, price, volume, order_type)`: 买入开仓。
*   `sell(context, symbol, price, volume, order_type)`: 卖出开仓。
*   `self.sdk`: 访问数据 SDK 的代理对象 (自动注入 Context)。

## 2. 核心对象 (Objects)

定义在 `strategy_spec.objects` 中。

### Context (上下文)

`Context` 对象贯穿整个策略生命周期，用于存储状态和传递信息。

*   `portfolio`: 投资组合信息（资金、持仓）。
*   `current_dt`: 当前回测/实盘时间。
*   `run_params`: 运行参数。

### 市场数据

*   **Bar**: K线数据 (symbol, timestamp, open, high, low, close, volume, etc.)
*   **Tick**: 快照数据 (symbol, timestamp, price, volume, bid/ask quotes)

### 交易数据

*   **Order**: 订单详情。
    *   `symbol`: 标的代码。
    *   `direction_type`: 买卖方向 (`BUY`, `SELL`)。
    *   `order_type`: 订单类型 (`MARKET`, `LIMIT`, `STOP_MARKET`, `STOP_LIMIT`)。
    *   `status`: 订单状态 (`OPEN`, `FILLED`, `CANCELED`, etc.)。

## 3. 编写策略示例

```python
from strategy_spec.strategy import Strategy
from strategy_spec.objects import Context, Bar, OrderType

class MyStrategy(Strategy):
    def on_init(self, context: Context):
        # 初始化配置
        print("策略初始化")

    def on_start(self, context: Context):
        # 策略启动
        pass

    def on_timer(self, context: Context):
        # 定时逻辑
        # 使用 self.sdk 调用数据接口
        # 注意: self.sdk 会自动注入 context
        try:
            df = self.sdk.get_history_kline("BTC/USDT")
        except Exception as e:
            pass
        
        # 下单
        self.buy(context, "BTC/USDT", 50000, 0.1)
```

## 4. 策略配置规范 (Strategy Config)

策略通常需要一个 YAML 配置文件来定义运行时参数（如触发方式、时间间隔等）。

### 配置文件结构示例

```yaml
# 策略类名 (必须)
strategy_class: "MyStrategy"

# SDK 后端 (可选, 默认为 engine_mode 决定)
sdk_backend: "mock" # or "real", "backtrader"

# 触发器配置 (Trigger Config)
trigger:
  type: "timer" # 触发类型: timer (定时), event (事件)
  timer_cfg:
    interval: "2s" # 时间间隔: s=秒, m=分, h=时

# 自定义策略参数 (会注入到 context.strategy_params)
params:
  symbol: "BTC/USDT"
  ma_window: 10
```

### 注意事项

*   **回测模式下的 Timer 触发**:
    在回测模式 (Backtest Mode) 下，虽然配置了 `interval: 2s`，但策略的触发频率受限于回测数据的最小分辨率 (Bar Resolution)。
    *   如果数据是 1分钟 Bar，那么 `on_timer` 依然是 2s 触发一次时，bar 的 OHCLV **并没有任何变化**。
    *   请在编写回测策略时务必注意这一点。
