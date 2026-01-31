# 策略目录

本目录用于存放所有策略实现。

## 目录结构

每个策略应该有自己的子目录，包含以下文件：

```
strategies/
├── strategy_name/              # 策略名称（小写，下划线分隔）
│   ├── config.yaml             # 策略配置文件（必需）
│   ├── strategy_name_strategy.py  # 策略实现文件（必需）
│   └── README.md               # 策略说明文档（可选）
│
├── dual_ma/                    # 示例：双均线策略
│   ├── config.yaml
│   └── dual_ma_strategy.py
│
└── README.md                   # 本文件
```

## 命名规范

- **目录名**：小写字母，使用下划线分隔，例如：`dual_ma`, `momentum_strategy`
- **策略文件**：`{strategy_name}_strategy.py`，例如：`dual_ma_strategy.py`
- **配置文件**：`config.yaml`

## 配置文件格式

每个策略目录必须包含 `config.yaml`，格式如下：

```yaml
# 策略类名（必须）
strategy_class: "StrategyClassName"

# SDK 后端（可选，默认为 mock）
sdk_backend: "mock"  # 或 "real"

# 触发器配置
trigger:
  type: "timer"  # 或 "event"
  timer_cfg:
    interval: "5s"  # 时间间隔

# 策略参数（会注入到 context.strategy_params）
params:
  symbol: "BTC/USDT"
  # 其他自定义参数...
```

## 策略文件格式

策略文件必须继承 `Strategy` 基类：

```python
from strategy_spec.strategy import Strategy
from strategy_spec.objects import Context, Bar, OrderOp

class YourStrategy(Strategy):
    def on_init(self, context: Context):
        # 初始化逻辑
        pass
    
    def on_start(self, context: Context):
        # 启动逻辑
        pass
    
    def on_bar(self, context: Context, bar: Bar) -> List[OrderOp]:
        # 处理 K 线数据
        return []
    
    # ... 其他必需的方法
```

## 运行策略

使用运行引擎执行策略：

```bash
python run_strategy.py strategies/your_strategy/config.yaml
```

## 示例

参考 `example/dual_ma/` 目录中的双均线策略示例。
