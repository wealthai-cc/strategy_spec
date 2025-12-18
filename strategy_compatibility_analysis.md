# double_mean.py 策略兼容性分析报告

## 结论

**✅ 引擎框架基本支持该策略运行，但存在一个关键问题需要修复：`OrderCost` 类未被注入到策略模块中。**

## 详细分析

### ✅ 已完全支持的功能

1. **`from wealthdata import *`** ✅
   - `wealthdata` 模块已实现，包含 `get_bars`, `get_trades` 等函数

2. **`set_benchmark('000300.XSHG')`** ✅
   - 已实现：`engine/compat/config.py` 中的 `set_benchmark` 函数

3. **`set_option('use_real_price', True)`** ✅
   - 已实现：`engine/compat/config.py` 中的 `set_option` 函数

4. **`log.info(...)`** ✅
   - 已实现：`engine/compat/log.py` 中的 `Log` 类
   - 已注入：`engine/loader/loader.py` 中注入 `log` 对象

5. **`set_order_cost(...)`** ✅
   - 已实现：`engine/compat/config.py` 中的 `set_order_cost` 函数
   - 已注入：`engine/loader/loader.py` 中注入 `set_order_cost` 函数

6. **`run_daily(...)`** ✅
   - 已实现：`engine/compat/scheduler.py` 中的 `create_run_daily_function`
   - 已注入：`engine/loader/loader.py` 中注入 `run_daily` 函数
   - 支持 `time='before_open'`, `'open'`, `'after_close'`

7. **`context.current_dt.time()`** ✅
   - 已实现：`engine/context/context.py` 中的 `Context.current_dt` 属性
   - 返回 `datetime` 对象，支持 `.time()` 方法

8. **`g.security = '000001.XSHE'`** ✅
   - 已实现：`engine/compat/g.py` 中的 `create_g_object`
   - 已注入：`engine/loader/loader.py` 中注入 `g` 对象
   - 使用 `SimpleNamespace`，支持任意属性赋值

9. **`get_bars(security, count=5, unit='1d', fields=['close'])`** ✅
   - 已实现：`engine/wealthdata/wealthdata.py` 中的 `get_bars` 函数
   - 支持 `unit` 参数（JoinQuant 兼容）
   - 返回 pandas DataFrame，支持 `['close']` 列访问

10. **`close_data['close'].mean()`** ✅
    - pandas DataFrame 操作，完全支持

11. **`close_data['close'][-1]`** ✅
    - pandas Series 索引操作，完全支持

12. **`context.portfolio.available_cash`** ✅
    - 已实现：`engine/context/context.py` 中的 `Portfolio.available_cash` 属性
    - 从 `account.available_margin` 或 `account.balances` 计算

13. **`context.portfolio.positions_value`** ✅
    - 已实现：`engine/context/context.py` 中的 `Portfolio.positions_value` 属性

14. **`context.portfolio.positions[security].closeable_amount`** ✅
    - 已实现：`engine/context/context.py` 中的 `Position` 类和 `PositionsDict` 类
    - 支持属性访问，不存在时返回默认值（不抛 KeyError）

15. **`order_value(security, cash)`** ✅
    - 已实现：`engine/compat/order.py` 中的 `order_value` 函数
    - 已注入：`engine/loader/loader.py` 中注入 `order_value` 函数

16. **`order_target(security, 0)`** ✅
    - 已实现：`engine/compat/order.py` 中的 `order_target` 函数
    - 已注入：`engine/loader/loader.py` 中注入 `order_target` 函数

17. **`get_trades()`** ✅
    - 已实现：`engine/wealthdata/wealthdata.py` 中的 `get_trades` 函数
    - 返回字典格式的成交记录

### ❌ 需要修复的问题

1. **`OrderCost` 类未被注入** ❌
   - **问题**：策略代码第 25 行使用 `OrderCost(close_tax=0.001, ...)`，但 `OrderCost` 类未被注入到策略模块
   - **影响**：策略执行时会抛出 `NameError: name 'OrderCost' is not defined`
   - **修复方案**：需要在 `engine/loader/loader.py` 的 `_inject_compatibility_objects` 方法中注入 `OrderCost` 类
   - **位置**：`strategy/__init__.py` 中有类型提示定义，但实际类需要创建并注入

## 修复建议

在 `engine/loader/loader.py` 的 `_inject_compatibility_objects` 方法中添加：

```python
# 注入 OrderCost 类
from types import SimpleNamespace

class OrderCost:
    """Order cost configuration (JoinQuant compatibility)."""
    def __init__(
        self,
        close_tax: float = 0,
        open_commission: float = 0,
        close_commission: float = 0,
        min_commission: float = 0
    ):
        self.close_tax = close_tax
        self.open_commission = open_commission
        self.close_commission = close_commission
        self.min_commission = min_commission

self._module.OrderCost = OrderCost
```

## 总结

- **支持度**：17/18 功能已实现（94.4%）
- **关键问题**：`OrderCost` 类缺失，会导致策略初始化失败
- **修复难度**：简单（只需添加一个类定义和一行注入代码）
- **修复后**：策略应该可以完全正常运行



