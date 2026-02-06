import logging
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from strategy_sdk.sdk_frontend_base import StrategySDKBase

from strategy_spec.objects import (
    Context, Bar, Tick, Order, OrderOp
)

class Strategy(ABC):
    """
    事件驱动策略基类。
    参考了 vn.py, Backtrader 等主流量化框架的设计。
    
    生命周期:
    on_init -> on_start -> [事件循环: on_bar/tick/order/timer] -> on_stop
    """

    def __init__(self):
        # SDK 实例，由 Engine 注入
        # 类型为 StrategySDKBase (实际上是 SDKProxy)
        self.sdk: Optional['StrategySDKBase'] = None
        
        # 初始化日志
        self.log_level = "INFO"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(self.log_level)

    def set_log_level(self, level: str):
        """
        设置日志级别
        """
        self.log_level = level.upper()
        self.logger.setLevel(self.log_level)

    @abstractmethod
    def on_init(self, context: Context):
        """
        策略初始化时调用。
        用于加载配置，初始化指标等。
        """
        pass

    @abstractmethod
    def on_start(self, context: Context):
        """
        策略开始执行时调用。
        """
        pass

    @abstractmethod
    def on_stop(self, context: Context):
        """
        策略停止时调用。
        """
        pass

    # --- 事件处理函数 ---
    # 策略应该重写这些方法来实现交易逻辑。
    # 它们可以返回 OrderOp 列表

    @abstractmethod
    def on_bar(self, context: Context, bar: Bar) -> List[OrderOp]:
        """
        当新的 Bar (K线) 到达时调用。
        """
        pass

    @abstractmethod
    def on_tick(self, context: Context, tick: Tick) -> List[OrderOp]:
        """
        当新的 Tick 到达时调用。
        """
        pass

    @abstractmethod
    def on_order_status(self, context: Context, order: Order) -> List[OrderOp]:
        """
        当订单状态发生变化时调用。
        """
        pass

    @abstractmethod
    def on_timer(self, context: Context) -> List[OrderOp]:
        """
        如果启用了定时器，则周期性调用。
        """
        pass
