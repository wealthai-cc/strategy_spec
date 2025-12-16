# Strategy Execution Engine

策略执行引擎框架，参考 JoinQuant 平台设计，提供简化的策略开发接口。

## 架构

```
策略管理系统
    ↓ (gRPC)
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
    ├── handle_bar(context, bar)
    ├── on_order(context, order)
    └── on_risk_event(context, event)
```

## 核心组件

### 1. Context 对象 (`engine/context/`)

提供统一的接口：
- `context.account` - 账户信息
- `context.history(symbol, count, timeframe)` - 历史行情数据
- `context.order_buy()` / `context.order_sell()` - 下单接口
- `context.cancel_order()` - 撤单接口

### 2. 策略加载器 (`engine/loader/`)

加载 Python 策略文件并提取生命周期函数：
- `initialize(context)` - 必需
- `before_trading(context)` - 可选
- `handle_bar(context, bar)` - 可选
- `on_order(context, order)` - 可选
- `on_risk_event(context, event)` - 可选

### 3. 事件调度器 (`engine/dispatcher/`)

将 ExecRequest 触发事件映射到策略函数：
- `MARKET_DATA_TRIGGER_TYPE` → `handle_bar()`
- `ORDER_STATUS_TRIGGER_TYPE` → `on_order()`
- `RISK_MANAGE_TRIGGER_TYPE` → `on_risk_event()`

### 4. 生命周期管理器 (`engine/lifecycle/`)

管理策略生命周期函数调用：
- 确保 `initialize()` 只调用一次
- 管理 `before_trading()` 调用时机

### 5. 执行引擎 (`engine/engine.py`)

协调所有组件，执行策略逻辑。

### 6. gRPC 服务 (`engine/grpc_service.py`)

实现 StrategySpec gRPC 接口，包装执行引擎。

## 使用示例

### 编写策略

```python
# strategy.py
def initialize(context):
    context.symbol = "BTCUSDT"
    context.ma_period = 20
    context.quantity = 0.1

def handle_bar(context, bar):
    bars = context.history(context.symbol, context.ma_period, "1h")
    if len(bars) >= context.ma_period:
        ma = sum(float(b.close) for b in bars) / context.ma_period
        if float(bar.close) > ma:
            context.order_buy(context.symbol, context.quantity)
```

### 使用引擎

```python
from engine.engine import StrategyExecutionEngine

# 创建引擎
engine = StrategyExecutionEngine("strategy.py")

# 执行策略
exec_request = {
    "trigger_type": 1,  # MARKET_DATA_TRIGGER_TYPE
    "trigger_detail": {},
    "market_data_context": [...],
    "account": {...},
    "incomplete_orders": [],
    "completed_orders": [],
    "exchange": "binance",
    "exec_id": "exec123",
    "strategy_param": {},
}

response = engine.execute(exec_request)
print(response["order_op_event"])
```

## 测试

运行测试：

```bash
pytest tests/
```

## 安装

```bash
pip install -r requirements.txt
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black engine/ tests/
```

