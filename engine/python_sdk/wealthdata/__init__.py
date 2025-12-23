"""
wealthdata SDK module - Data access methods for wealthdata package.

This module provides data access methods that are independent of the
strategy execution engine context, using the data adapter pattern.
"""

from .data_access import (
    get_price,
    get_bars,
    get_trades,
    get_all_securities,
    get_trade_days,
    get_index_stocks,
    get_index_weights,
    get_fundamentals,
    get_industry,
)

__all__ = [
    'get_price',
    'get_bars',
    'get_trades',
    'get_all_securities',
    'get_trade_days',
    'get_index_stocks',
    'get_index_weights',
    'get_fundamentals',
    'get_industry',
]

