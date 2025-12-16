"""
策略模块类型提示

这个文件为策略文件提供类型提示，让编辑器识别运行时注入的函数。
这些函数在策略执行时由引擎自动注入，不需要导入。
"""

from typing import Any, Callable, Optional

# 全局变量对象
class GObject:
    """全局变量对象，用于存储策略状态"""
    pass

g: GObject = GObject()

# 日志模块
class Log:
    """日志模块"""
    def info(self, msg: str) -> None: ...
    def warn(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def debug(self, msg: str) -> None: ...
    def set_level(self, category: str, level: str) -> None: ...

log: Log = Log()

# 定时运行函数
def run_daily(
    func: Callable,
    time: str = 'open',
    reference_security: Optional[str] = None
) -> None:
    """
    注册定时运行函数
    
    Args:
        func: 要执行的函数
        time: 执行时间点 ('before_open', 'open', 'after_close')
        reference_security: 参考标的（用于市场类型识别）
    """
    ...

# 下单函数
def order_value(symbol: str, value: float, price: Optional[float] = None) -> Any:
    """
    按金额下单
    
    Args:
        symbol: 交易对或股票代码
        value: 交易金额
        price: 限价（可选）
    """
    ...

def order_target(symbol: str, target_qty: float, price: Optional[float] = None) -> Any:
    """
    调整到目标持仓
    
    Args:
        symbol: 交易对或股票代码
        target_qty: 目标数量
        price: 限价（可选）
    """
    ...

# 配置函数
def set_benchmark(security: str) -> None:
    """设置基准"""
    ...

def set_option(option_name: str, value: Any) -> None:
    """设置选项"""
    ...

class OrderCost:
    """订单成本配置"""
    def __init__(
        self,
        close_tax: float = 0,
        open_commission: float = 0,
        close_commission: float = 0,
        min_commission: float = 0
    ) -> None: ...

def set_order_cost(cost: OrderCost, type: str = 'stock') -> None:
    """设置订单成本"""
    ...

