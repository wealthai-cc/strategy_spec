# 策略文件运行说明

## 重要提示

策略文件**不应该直接运行**，应该通过策略执行引擎运行。

策略文件依赖于：
- `wealthdata` 模块（在项目根目录）
- 策略执行引擎提供的 Context 对象
- 数据适配器注册机制

## 如果必须直接运行（用于测试）

### 方法 1：从项目根目录运行

```bash
# 在项目根目录执行
cd /Users/spencerjin/Documents/wealthai_strategy_spec
python strategy/double_mean.py
```

### 方法 2：设置 PYTHONPATH

```bash
# 设置 PYTHONPATH 包含项目根目录
export PYTHONPATH=/Users/spencerjin/Documents/wealthai_strategy_spec:$PYTHONPATH
python strategy/double_mean.py
```

### 方法 3：在策略文件开头添加路径

```python
import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wealthdata import *
```

## 正确的运行方式

策略文件应该通过策略执行引擎运行：

```python
from engine.engine import StrategyExecutionEngine

engine = StrategyExecutionEngine('strategy/double_mean.py')
engine.load_strategy()

# 执行策略
exec_request = {
    "trigger_type": 1,  # MARKET_DATA_TRIGGER_TYPE
    "market_data_context": [...],
    "account": {...},
    # ...
}

response = engine.execute(exec_request)
```

## 为什么不能直接运行？

1. **缺少 Context**：策略函数需要 Context 对象，这由引擎提供
2. **缺少数据适配器**：SDK 方法需要数据适配器，这由引擎注册
3. **缺少市场数据**：策略需要 ExecRequest 中的市场数据

直接运行策略文件会导致：
- `ModuleNotFoundError: No module named 'wealthdata'`（如果路径不对）
- `RuntimeError: Data adapter not registered`（即使路径对了）


