"""
wealthdata - JoinQuant jqdata compatibility layer

This module provides compatibility with JoinQuant's jqdatasdk API,
enabling zero-code-modification migration for JoinQuant strategies.

Usage:
    import wealthdata  # instead of import jqdatasdk
    
    def handle_bar(context, bar):
        df = wealthdata.get_price('BTCUSDT', count=20, frequency='1h')
        ma = df['close'].mean()
        # ... rest of code unchanged
"""

from .wealthdata import (
    get_price,
    get_bars,
    get_all_securities,
    get_trade_days,
    get_index_stocks,
    get_index_weights,
    get_fundamentals,
    get_industry,
    get_trades,
    set_context,
    get_context,
    clear_context,
    bars_to_dataframe,
)

__all__ = [
    'get_price',
    'get_bars',
    'get_all_securities',
    'get_trade_days',
    'get_index_stocks',
    'get_index_weights',
    'get_fundamentals',
    'get_industry',
    'get_trades',
    'set_context',
    'get_context',
    'clear_context',
    'bars_to_dataframe',
]

