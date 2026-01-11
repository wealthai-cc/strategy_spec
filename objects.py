from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import datetime

# --- Aligning with trade_server.proto ---

class DirectionType(Enum):
    INVALID_DIRECTION_TYPE = 0
    BUY_DIRECTION_TYPE = 1               # 买入
    SELL_DIRECTION_TYPE = 2              # 卖出

class OrderType(Enum):
    INVALID_ORDER_TYPE = 0
    MARKET_ORDER_TYPE = 1          # 市价单
    LIMIT_ORDER_TYPE = 2           # 限价单
    STOP_MARKET_ORDER_TYPE = 3     # 止损市价单
    STOP_LIMIT_ORDER_TYPE = 4      # 止损限价单

class TimeInForceType(Enum):
    INVALID_TIF_TYPE = 0
    GTC_TIF_TYPE = 1 # Good-Till-Cancelled
    IOC_TIF_TYPE = 2 # Immediate-Or-Cancel
    FOK_TIF_TYPE = 3 # Fill-Or-Kill

class OrderStatusType(Enum):
    INVALID_ORDER_STATUS_TYPE = 0
    OPEN_ORDER_STATUS_TYPE = 1             # NEW
    PARTIALLY_FILLED_ORDER_STATUS_TYPE = 2
    FILLED_ORDER_STATUS_TYPE = 3
    CANCELED_ORDER_STATUS_TYPE = 4
    PENDING_CANCEL_ORDER_STATUS_TYPE = 5
    REJECTED_ORDER_STATUS_TYPE = 6
    EXPIRED_ORDER_STATUS_TYPE = 7



class TimeUnit(Enum):
    MINUTE = 'm'
    HOUR = 'h'
    DAY = 'd'
    WEEK = 'w'

@dataclass
class TimeFrame:
    amount: int
    unit: TimeUnit
    
    def __str__(self):
        return f"{self.amount}{self.unit.value}"
        
    def to_ktype(self) -> str:
        """
        将 TimeFrame 转换为 get_history_kline 所需的 ktype 字符串。

        返回值示例：K_1M、K_5M、K_60M、K_DAY、K_WEEK。
        若 unit/amount 组合不被当前 SDK 支持，则返回空字符串。
        """
        supported_minute_amounts = {1, 3, 5, 15, 30, 60}

        if self.unit == TimeUnit.MINUTE:
            if self.amount in supported_minute_amounts:
                return f"K_{self.amount}M"
            return ""

        if self.unit == TimeUnit.HOUR:
            minutes = self.amount * 60
            if minutes in supported_minute_amounts:
                return f"K_{minutes}M"
            return ""

        if self.unit == TimeUnit.DAY:
            return "K_DAY" if self.amount == 1 else ""

        if self.unit == TimeUnit.WEEK:
            return "K_WEEK" if self.amount == 1 else ""

        return ""

@dataclass
class Bar:
    symbol: str
    timestamp: datetime.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    interval: TimeFrame = None

@dataclass
class Tick:
    symbol: str
    timestamp: datetime.datetime
    price: float
    volume: float
    bid_price_1: float
    ask_price_1: float
    bid_volume_1: float
    ask_volume_1: float

@dataclass
class Order:
    """
    Corresponds to trpc.wealthai.trade_server.Order
    """
    # Essential fields for creating an order
    symbol: str
    direction_type: DirectionType
    order_type: OrderType
    size: str # String to avoid float precision issues
    
    # Optional / Conditional fields
    price: str = "0"          # Limit Price
    stop_price: str = "0"     # Stop Price
    quote_order_qty: str = "0" # Quote Order Qty (Market Buy by Value)
    time_in_force: TimeInForceType = TimeInForceType.GTC_TIF_TYPE
    
    # System fields (assigned by engine/server)
    order_id: str = ""
    unique_id: str = "" # Client ID
    create_ts: int = 0
    status: OrderStatusType = OrderStatusType.INVALID_ORDER_STATUS_TYPE
    executed_size: str = "0"
    cummulative_quote_qty: str = "0"
    update_ts: int = 0
    
class OrderOpType(Enum):
    CREATE = 1
    CANCEL = 2
    MODIFY = 3

@dataclass
class OrderOp:
    op_type: OrderOpType
    order: Optional[Order] = None
    order_id: str = "" # For cancel/modify
    params: Dict = None # Extra params

@dataclass
class Position:
    symbol: str
    total_volume: float = 0.0
    frozen_volume: float = 0.0
    available_volume: float = 0.0
    average_price: float = 0.0

class Portfolio(object):
    def __init__(self):
        self.total_cash = 0.0
        self.frozen_cash = 0.0
        self.available_cash = 0.0
        self.positions: Dict[str, Position] = {}
        self.total_value = 0.0
        self.positions_value = 0.0

class Context(object):
    """
    Strategy Context Environment
    """
    def __init__(self):
        self.portfolio: Portfolio = Portfolio()  # 投资组合快照：现金、持仓、总资产等（单账户/单组合语义）
        self.current_dt: Optional[datetime.datetime] = None  # 当前引擎时间（回测为当前 bar 时间；实盘为事件时间）
        self.cash: float = 0.0  # 账户现金总量（通常等价于 portfolio.total_cash；用于展示/统计）
        self.available_cash: float = 0.0  # 可下单现金（通常等价于 portfolio.available_cash；策略风控应优先使用）
        self.universe: List[str] = []  # 策略关注的标的列表（订阅/回测加载的 symbols）
        self.strategy_params: Dict = {}  # 策略参数（来自配置或上层 ExecRequest.strategy_param）
        self._order_ops: List[OrderOp] = []  # 订单操作历史（归档用途；不要当作执行队列）

    def add_order_op(self, op: OrderOp):
        """
        Record an order operation for history/archival purposes.
        Do NOT use this for order execution queue.
        """
        self._order_ops.append(op)

    def get_order_ops_history(self) -> List[OrderOp]:
        """
        Return the history of order operations.
        """
        return self._order_ops[:]
