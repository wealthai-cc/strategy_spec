"""
wealthdata module - JoinQuant jqdata compatibility layer

Provides module-level API functions compatible with jqdatasdk,
enabling direct copy-paste of JoinQuant strategy code.
"""

import threading
import warnings
from typing import Optional, List, Dict, Any
import pandas as pd

# Thread-local storage for current execution Context
_context_local = threading.local()


def set_context(context: Any) -> None:
    """
    Set current execution context (called by execution engine).
    
    Args:
        context: Context object from strategy execution
    """
    _context_local.context = context


def get_context() -> Optional[Any]:
    """
    Get current execution context (called by wealthdata functions).
    
    Returns:
        Context object if available, None otherwise
    
    Raises:
        RuntimeError: If context is not available
    """
    context = getattr(_context_local, 'context', None)
    if context is None:
        raise RuntimeError(
            "Context not available. Ensure strategy is executed by the execution engine. "
            "The engine should set context before calling strategy functions."
        )
    return context


def clear_context() -> None:
    """
    Clear current execution context (called by execution engine after execution).
    """
    if hasattr(_context_local, 'context'):
        delattr(_context_local, 'context')


def bars_to_dataframe(bars: List[Any]) -> pd.DataFrame:
    """
    Convert Bar objects to pandas DataFrame (compatible with jqdata format).
    
    Args:
        bars: List of Bar objects
    
    Returns:
        pandas DataFrame with columns: open, high, low, close, volume
        Index is close_time from Bar objects
    """
    if not bars:
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    data = []
    for bar in bars:
        data.append({
            'time': bar.close_time,
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': float(bar.volume),
        })
    
    df = pd.DataFrame(data)
    if len(df) > 0:
        df.set_index('time', inplace=True)
    return df


def get_price(
    symbol: str,
    count: Optional[int] = None,
    end_date: Optional[str] = None,
    frequency: str = '1h',
    fields: Optional[List[str]] = None,
    skip_paused: bool = False,
    fq: str = 'pre'
) -> pd.DataFrame:
    """
    Get price data, compatible with jqdatasdk.get_price().
    
    This function provides the same interface as jqdatasdk.get_price(),
    enabling direct copy-paste of JoinQuant strategy code.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        count: Number of bars to retrieve (default: 20)
        end_date: End date (limited by ExecRequest data range, may be ignored)
        frequency: Time resolution ('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w')
        fields: Data fields to return (default: all - open, high, low, close, volume)
        skip_paused: Ignored (not applicable for crypto trading)
        fq: Ignored (not applicable for crypto trading)
    
    Returns:
        pandas DataFrame with columns: open, high, low, close, volume
        Index is time (close_time from Bar objects)
    
    Raises:
        RuntimeError: If context is not available
        ValueError: If symbol or frequency is invalid
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            df = wealthdata.get_price('BTCUSDT', count=20, frequency='1h')
            ma = df['close'].mean()
        ```
    """
    context = get_context()
    
    # Validate parameters
    if not symbol:
        raise ValueError("symbol parameter is required")
    
    # Map frequency to timeframe (direct mapping for common values)
    timeframe = frequency
    
    # Use count or default to 20
    count = count or 20
    
    # Warn about unsupported parameters
    if end_date is not None:
        warnings.warn(
            f"end_date parameter ({end_date}) is limited by ExecRequest data range. "
            "Only available data will be returned.",
            UserWarning
        )
    
    if skip_paused:
        warnings.warn(
            "skip_paused parameter is not applicable for crypto trading and will be ignored.",
            UserWarning
        )
    
    if fq != 'pre':
        warnings.warn(
            f"fq parameter ({fq}) is not applicable for crypto trading and will be ignored.",
            UserWarning
        )
    
    # Get bars from context
    bars = context.history(symbol, count, timeframe)
    
    # Convert to DataFrame
    df = bars_to_dataframe(bars)
    
    # Filter fields if specified
    if fields is not None:
        available_fields = ['open', 'high', 'low', 'close', 'volume']
        valid_fields = [f for f in fields if f in available_fields]
        if valid_fields:
            df = df[valid_fields]
        else:
            warnings.warn(
                f"None of the requested fields {fields} are available. "
                "Returning all fields.",
                UserWarning
            )
    
    return df


def get_bars(
    symbol: str,
    count: Optional[int] = None,
    end_date: Optional[str] = None,
    frequency: str = '1h',
    fields: Optional[List[str]] = None,
    skip_paused: bool = False,
    fq: str = 'pre'
) -> pd.DataFrame:
    """
    Get bar data, compatible with jqdatasdk.get_bars().
    
    This function is an alias for get_price() with the same interface.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        count: Number of bars to retrieve (default: 20)
        end_date: End date (limited by ExecRequest data range, may be ignored)
        frequency: Time resolution ('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w')
        fields: Data fields to return (default: all)
        skip_paused: Ignored (not applicable for crypto trading)
        fq: Ignored (not applicable for crypto trading)
    
    Returns:
        pandas DataFrame with columns: open, high, low, close, volume
        Index is time (close_time from Bar objects)
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            df = wealthdata.get_bars('BTCUSDT', count=20, frequency='1h')
            # Same as get_price()
        ```
    """
    # get_bars is essentially the same as get_price
    return get_price(
        symbol=symbol,
        count=count,
        end_date=end_date,
        frequency=frequency,
        fields=fields,
        skip_paused=skip_paused,
        fq=fq
    )

