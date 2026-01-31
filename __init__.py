"""
Strategy Specification (策略规范)

本模块定义了量化交易策略开发的标准接口、基类以及相关的数据结构。
"""

__version__ = "0.1.0"

from .strategy import Strategy
from .objects import (
    Context, Bar, Tick, Order, OrderOp,
    OrderOpType, DirectionType, OrderType, 
    OrderStatusType, TimeInForceType
)

__all__ = [
    "Strategy",
    "Context",
    "Bar",
    "Tick",
    "Order",
    "OrderOp",
    "OrderOpType",
    "DirectionType",
    "OrderType",
    "OrderStatusType",
    "TimeInForceType",
]
