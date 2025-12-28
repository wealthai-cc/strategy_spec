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
    interval: str = "1m"

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

class SubPortfolio(object):
    pass

class Portfolio(object):
    def __init__(self):
        self.cash = 0.0
        self.positions = {} # Dict[symbol, Position]
        self.total_value = 0.0
        self.positions_value = 0.0

class Context(object):
    """
    Strategy Context Environment
    """
    def __init__(self):
        self.portfolio: Portfolio = Portfolio()
        self.subportfolios: List[SubPortfolio] = []
        self.current_dt: Optional[datetime.datetime] = None
        self.universe: List[str] = []
        self.run_params: Dict = {}
        self.strategy_params: Dict = {}
        self._order_ops: List[OrderOp] = []
        self.data_provider = None 
        self.trade_provider = None

    def add_order_op(self, op: OrderOp):
        self._order_ops.append(op)

    def get_order_ops(self) -> List[OrderOp]:
        ops = self._order_ops[:]
        self._order_ops.clear()
        return ops
