"""
wealthdata - JoinQuant jqdata compatibility layer

This is a top-level module alias that allows strategies to import wealthdata
directly without needing to know about the engine package structure.

Usage in strategies:
    import wealthdata  # Works directly!
    
    def handle_bar(context, bar):
        df = wealthdata.get_price('BTCUSDT', count=20, frequency='1h')
"""

# Import all public APIs from engine.wealthdata
from engine.wealthdata import (
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

