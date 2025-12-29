from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
import datetime
import uuid

if TYPE_CHECKING:
    from strategy_sdk.sdk_frontend_base import DataSDKBase

from strategy_spec.objects import (
    Context, Bar, Tick, Order, OrderOp, OrderOpType, 
    DirectionType, OrderType, OrderStatusType, TimeInForceType
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
        # 类型为 DataSDKBase (实际上是 SDKProxy)
        self.sdk: Optional['DataSDKBase'] = None

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

    # --- 辅助方法 ---
    # 这些辅助方法生成 OrderOps 并返回。

    def buy(self, context: Context, symbol: str, price: float, volume: float, order_type: OrderType = OrderType.LIMIT_ORDER_TYPE) -> OrderOp:
        """
        买入开仓
        """
        return self._create_order(context, symbol, DirectionType.BUY_DIRECTION_TYPE, price, volume, order_type)

    def sell(self, context: Context, symbol: str, price: float, volume: float, order_type: OrderType = OrderType.LIMIT_ORDER_TYPE) -> OrderOp:
        """
        卖出开仓
        """
        return self._create_order(context, symbol, DirectionType.SELL_DIRECTION_TYPE, price, volume, order_type)

    def _create_order(self, context: Context, symbol: str, direction: DirectionType, price: float, volume: float, order_type: OrderType) -> OrderOp:
        order = Order(
            order_id="", # 系统分配
            unique_id=str(uuid.uuid4()), # 客户端生成的唯一ID
            symbol=symbol,
            direction_type=direction,
            order_type=order_type,
            price=str(price),
            size=str(volume),
            status=OrderStatusType.OPEN_ORDER_STATUS_TYPE,
            time_in_force=TimeInForceType.GTC_TIF_TYPE # 默认 GTC
        )
        op = OrderOp(op_type=OrderOpType.CREATE, order=order)
        return op
