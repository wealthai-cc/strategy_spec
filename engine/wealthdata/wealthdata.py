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
        Index is DatetimeIndex from close_time (allows negative index access like df['close'][-1])
    """
    if not bars:
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    data = []
    timestamps = []
    for bar in bars:
        data.append({
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': float(bar.volume),
        })
        # Convert timestamp (milliseconds) to datetime
        timestamps.append(pd.Timestamp(bar.close_time, unit='ms'))
    
    df = pd.DataFrame(data, index=pd.DatetimeIndex(timestamps))
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
    frequency: Optional[str] = None,
    unit: Optional[str] = None,  # JoinQuant compatibility: alias for frequency
    fields: Optional[List[str]] = None,
    skip_paused: bool = False,
    fq: str = 'pre'
) -> pd.DataFrame:
    """
    Get bar data, compatible with jqdatasdk.get_bars().
    
    This function is an alias for get_price() with the same interface.
    Supports both 'frequency' and 'unit' parameters (unit is an alias for frequency).
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        count: Number of bars to retrieve (default: 20)
        end_date: End date (limited by ExecRequest data range, may be ignored)
        frequency: Time resolution ('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w')
        unit: JoinQuant compatibility: alias for frequency parameter
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
            # Using frequency parameter
            df = wealthdata.get_bars('BTCUSDT', count=20, frequency='1h')
            # Using unit parameter (JoinQuant compatibility)
            df = wealthdata.get_bars('BTCUSDT', count=20, unit='1d')
        ```
    """
    # Handle unit parameter (JoinQuant compatibility)
    if unit is not None:
        if frequency is not None and frequency != unit:
            raise ValueError(
                f"Cannot specify both 'frequency' ({frequency}) and 'unit' ({unit}) "
                "with different values. Use only one parameter."
            )
        frequency = unit
    
    # Default frequency if not provided
    if frequency is None:
        frequency = '1h'
    
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


def get_all_securities(
    types: Optional[List[str]] = None,
    date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get all securities (trading pairs) information, compatible with jqdatasdk.get_all_securities().
    
    This function extracts all unique trading pairs from the current ExecRequest's
    market_data_context and returns them in a format compatible with jqdatasdk.
    
    Args:
        types: Security types (e.g., ['stock']), ignored for crypto (all are crypto trading pairs)
        date: Date string, ignored (data is from current context)
    
    Returns:
        pandas DataFrame with columns:
        - display_name: Trading pair display name (same as name)
        - name: Trading pair symbol (e.g., 'BTCUSDT')
        - start_date: Not applicable (None or empty)
        - end_date: Not applicable (None, meaning still trading)
        - type: 'crypto' (all are crypto trading pairs)
        
        DataFrame index is the trading pair symbol (name)
    
    Raises:
        RuntimeError: If context is not available
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            df = wealthdata.get_all_securities()
            print(df)  # Shows all available trading pairs
        ```
    """
    context = get_context()
    
    # Warn about unsupported parameters
    if types is not None:
        warnings.warn(
            "types parameter is not applicable for cryptocurrency trading and will be ignored. "
            "All securities are crypto trading pairs.",
            UserWarning
        )
    
    if date is not None:
        warnings.warn(
            f"date parameter ({date}) is ignored. Data is from current ExecRequest context.",
            UserWarning
        )
    
    # Extract all unique symbols from market_data_context
    symbols = set()
    for market_context in context._market_data_context:
        symbol = market_context.get("symbol")
        if symbol:
            symbols.add(symbol)
    
    # Build DataFrame matching jqdatasdk format
    if not symbols:
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=['display_name', 'name', 'start_date', 'end_date', 'type'])
    
    data = []
    for symbol in sorted(symbols):  # Sort for consistent output
        data.append({
            'display_name': symbol,  # For crypto, display name is same as symbol
            'name': symbol,
            'start_date': None,  # Not applicable for crypto
            'end_date': None,  # None means still trading
            'type': 'crypto',
        })
    
    df = pd.DataFrame(data)
    df.set_index('name', inplace=True)
    return df


def get_index_stocks(
    index_symbol: str,
    date: Optional[str] = None
) -> List[str]:
    """
    Get index constituent stocks (trading pairs), compatible with jqdatasdk.get_index_stocks().
    
    This function returns the list of trading pair symbols that are constituents of the index.
    
    Args:
        index_symbol: Index identifier (e.g., 'BTC_INDEX', 'ETH_INDEX', 'DEFI_INDEX')
        date: Date string, ignored (returns current composition)
    
    Returns:
        List of trading pair symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
        Returns empty list if index not found
    
    Raises:
        RuntimeError: If context is not available
        ValueError: If index_symbol is empty
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            # Get BTC index constituents
            stocks = wealthdata.get_index_stocks('BTC_INDEX')
            print(stocks)  # ['BTCUSDT', 'ETHUSDT', ...]
        ```
    """
    get_context()  # Verify context is available
    
    if not index_symbol:
        raise ValueError("index_symbol parameter is required")
    
    if date is not None:
        warnings.warn(
            f"date parameter ({date}) is ignored. Returns current index composition.",
            UserWarning
        )
    
    # Import index configuration
    from .index_config import get_index_composition
    
    composition = get_index_composition(index_symbol)
    
    if not composition:
        warnings.warn(
            f"Index '{index_symbol}' not found. Returning empty list.",
            UserWarning
        )
    
    return composition


def get_index_weights(
    index_symbol: str,
    date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get index constituent weights, compatible with jqdatasdk.get_index_weights().
    
    This function returns the weights of trading pairs in the index.
    
    Args:
        index_symbol: Index identifier (e.g., 'BTC_INDEX', 'ETH_INDEX')
        date: Date string, ignored (returns current weights)
    
    Returns:
        pandas DataFrame with columns:
        - code: Trading pair symbol
        - weight: Weight in index (0.0 to 1.0)
        DataFrame index is the trading pair symbol (code)
        Returns empty DataFrame if index not found
    
    Raises:
        RuntimeError: If context is not available
        ValueError: If index_symbol is empty
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            # Get BTC index weights
            df = wealthdata.get_index_weights('BTC_INDEX')
            print(df)  # Shows weights for each trading pair
        ```
    """
    get_context()  # Verify context is available
    
    if not index_symbol:
        raise ValueError("index_symbol parameter is required")
    
    if date is not None:
        warnings.warn(
            f"date parameter ({date}) is ignored. Returns current index weights.",
            UserWarning
        )
    
    # Import index configuration
    from .index_config import get_index_weight_dict
    
    weight_dict = get_index_weight_dict(index_symbol)
    
    if not weight_dict:
        warnings.warn(
            f"Index '{index_symbol}' not found. Returning empty DataFrame.",
            UserWarning
        )
        return pd.DataFrame(columns=['code', 'weight'])
    
    # Build DataFrame matching jqdatasdk format
    data = []
    for symbol, weight in weight_dict.items():
        data.append({
            'code': symbol,
            'weight': weight,
        })
    
    df = pd.DataFrame(data)
    df.set_index('code', inplace=True)
    return df


def get_trade_days(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    count: Optional[int] = None
) -> List[str]:
    """
    Get trade days (dates), compatible with jqdatasdk.get_trade_days().
    
    Note: Cryptocurrency trades 7x24, so this returns all days in the range
    (including weekends, unlike stock market).
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        count: Number of days to return (if start_date not provided,
               returns last count days from available data range)
    
    Returns:
        List of date strings (YYYY-MM-DD format), sorted in ascending order
        (earliest to latest, matching jqdatasdk behavior)
    
    Raises:
        RuntimeError: If context is not available
        ValueError: If parameters are invalid
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            # Get all trade days in January 2025
            days = wealthdata.get_trade_days('2025-01-01', '2025-01-31')
            print(len(days))  # 31 (includes weekends for crypto)
        ```
    """
    from datetime import datetime, timedelta
    
    context = get_context()
    
    # Extract time range from market_data_context
    min_timestamp = None
    max_timestamp = None
    
    for market_context in context._market_data_context:
        bars = market_context.get("bars", [])
        for bar in bars:
            close_time = bar.get("close_time", 0)
            if close_time > 0:
                if min_timestamp is None or close_time < min_timestamp:
                    min_timestamp = close_time
                if max_timestamp is None or close_time > max_timestamp:
                    max_timestamp = close_time
    
    # If no data available, return empty list
    if min_timestamp is None or max_timestamp is None:
        warnings.warn(
            "No market data available in context. Cannot determine date range.",
            UserWarning
        )
        return []
    
    # Convert timestamps to datetime objects
    min_date = datetime.fromtimestamp(min_timestamp / 1000)
    max_date = datetime.fromtimestamp(max_timestamp / 1000)
    
    # Determine date range based on parameters
    if start_date and end_date:
        # Use provided date range
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    elif start_date:
        # From start_date to max available date
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = max_date
    elif count:
        # Last count days from available data
        end = max_date
        start = end - timedelta(days=count - 1)
    else:
        # Use available data range
        start = min_date
        end = max_date
    
    # Detect market type from context
    from engine.compat.market_type import detect_market_type, MarketType
    
    # Try to detect market type from first symbol in market_data_context
    market_type = MarketType.CRYPTO  # Default to crypto
    if context._market_data_context:
        first_context = context._market_data_context[0]
        symbol = first_context.get('symbol', '')
        if symbol:
            market_type = detect_market_type(symbol, context)
    
    # Generate dates based on market type
    dates = []
    current = start
    while current <= end:
        if market_type == MarketType.CRYPTO:
            # Cryptocurrency: include all days (7x24 trading)
            dates.append(current.strftime('%Y-%m-%d'))
        else:
            # Stock market: exclude weekends (Saturday=5, Sunday=6)
            # TODO: Also exclude holidays when trade_calendar is implemented
            if current.weekday() < 5:  # Monday=0 to Friday=4
                dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # Return in ascending order (earliest to latest, matching jqdatasdk)
    return sorted(dates)


def get_fundamentals(
    valuation: Any,
    statDate: Optional[str] = None,
    statDateCount: Optional[int] = None
) -> pd.DataFrame:
    """
    Get fundamentals data, compatible with jqdatasdk.get_fundamentals().
    
    Note: Financial data concept doesn't fully apply to cryptocurrency.
    jqdatasdk uses complex query objects (query(valuation).filter(...)),
    but for crypto we simplify this to return basic trading pair information
    or empty DataFrame with warning.
    
    Args:
        valuation: Query object (simplified for crypto - can accept None, dict, or basic object)
                  If dict, should contain 'code' key with trading pair symbol
        statDate: Stat date, ignored
        statDateCount: Stat date count, ignored
    
    Returns:
        pandas DataFrame with basic trading pair info (if available) or empty DataFrame
        Columns depend on what data is available (e.g., symbol, market_cap, volume_24h)
        Returns empty DataFrame with warning if financial data is not applicable
    
    Raises:
        RuntimeError: If context is not available
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            # Simplified usage (jqdatasdk uses complex query objects)
            df = wealthdata.get_fundamentals({'code': 'BTCUSDT'})
            # Returns basic info or empty DataFrame with warning
        ```
    """
    context = get_context()
    
    if statDate is not None:
        warnings.warn(
            f"statDate parameter ({statDate}) is ignored for cryptocurrency fundamentals.",
            UserWarning
        )
    
    if statDateCount is not None:
        warnings.warn(
            f"statDateCount parameter ({statDateCount}) is ignored for cryptocurrency fundamentals.",
            UserWarning
        )
    
    # Extract symbol from valuation if possible
    symbol = None
    if valuation is None:
        pass
    elif isinstance(valuation, dict):
        symbol = valuation.get('code')
    elif hasattr(valuation, 'code'):
        symbol = getattr(valuation, 'code', None)
    elif hasattr(valuation, '__iter__') and not isinstance(valuation, str):
        # Try to extract from iterable
        try:
            for item in valuation:
                if hasattr(item, 'code'):
                    symbol = getattr(item, 'code')
                    break
                elif isinstance(item, dict):
                    symbol = item.get('code')
                    break
        except (TypeError, AttributeError):
            pass
    
    # Warn that financial data doesn't fully apply
    warnings.warn(
        "Financial data concept doesn't fully apply to cryptocurrency. "
        "This function returns limited data or empty DataFrame. "
        "For crypto, consider using market data APIs instead.",
        UserWarning
    )
    
    # If we have a symbol, try to return basic info from context
    if symbol:
        # Check if symbol exists in market_data_context
        for market_context in context._market_data_context:
            if market_context.get("symbol") == symbol:
                # Return basic info DataFrame
                bars = market_context.get("bars", [])
                if bars:
                    latest_bar = bars[-1]
                    return pd.DataFrame([{
                        'code': symbol,
                        'close': float(latest_bar.get("close", 0)),
                        'volume': float(latest_bar.get("volume", 0)),
                        # Note: market_cap and other financial metrics not available
                    }])
    
    # Return empty DataFrame if no data available
    return pd.DataFrame(columns=['code', 'close', 'volume'])


def get_industry(
    security: str,
    date: Optional[str] = None
) -> str:
    """
    Get industry (category) for a security (trading pair), compatible with jqdatasdk.get_industry().
    
    This function returns the category/industry classification for a cryptocurrency trading pair.
    
    Args:
        security: Trading pair symbol (e.g., 'BTCUSDT')
        date: Date string, ignored (returns current category)
    
    Returns:
        Industry/category string (e.g., 'Layer1', 'DeFi', 'Layer2', 'Exchange')
        Returns empty string if category not found
    
    Raises:
        RuntimeError: If context is not available
        ValueError: If security is empty
    
    Example:
        ```python
        import wealthdata
        
        def handle_bar(context, bar):
            # Get category for BTC
            category = wealthdata.get_industry('BTCUSDT')
            print(category)  # 'Layer1'
        ```
    """
    get_context()  # Verify context is available
    
    if not security:
        raise ValueError("security parameter is required")
    
    if date is not None:
        warnings.warn(
            f"date parameter ({date}) is ignored. Returns current category.",
            UserWarning
        )
    
    # Import industry configuration
    from .industry_config import get_trading_pair_category
    
    category = get_trading_pair_category(security)
    
    if not category:
        warnings.warn(
            f"Category not found for trading pair '{security}'. Returning empty string.",
            UserWarning
        )
    
    return category


def get_trades() -> Dict[str, Dict[str, Any]]:
    """
    Get completed trade records, compatible with JoinQuant's get_trades().
    
    Returns a dictionary of completed trades, where each trade contains:
    - security: Trading symbol
    - price: Fill price
    - amount: Filled quantity
    - time: Trade time
    - order_id: Order ID
    
    Returns:
        Dictionary mapping order_id to trade record dictionary
        
    Raises:
        RuntimeError: If context is not available
    
    Example:
        ```python
        import wealthdata
        
        def after_market_close(context):
            trades = wealthdata.get_trades()
            for order_id, trade in trades.items():
                print(f"Trade: {trade['security']} @ {trade['price']}, qty: {trade['amount']}")
        ```
    """
    context = get_context()
    if context is None:
        raise RuntimeError(
            "No context available. get_trades() must be called during strategy execution."
        )
    
    trades = {}
    
    # Extract completed orders from context
    completed_orders = getattr(context, '_completed_orders', [])
    
    for order in completed_orders:
        # Only include filled orders
        status = order.status if hasattr(order, 'status') else order.get('status', 0)
        
        # Check if order is filled (status == FILLED, typically 3 or "FILLED")
        is_filled = False
        if isinstance(status, str):
            is_filled = status.upper() == 'FILLED'
        elif isinstance(status, int):
            # Assuming 3 is FILLED status (adjust based on actual enum)
            is_filled = status == 3
        
        if is_filled:
            # Get order details
            order_id = order.order_id if hasattr(order, 'order_id') else order.get('order_id', '')
            symbol = order.symbol if hasattr(order, 'symbol') else order.get('symbol', '')
            
            # Get fill price
            fill_price = None
            if hasattr(order, 'avg_fill_price'):
                fill_price = order.avg_fill_price
            elif isinstance(order, dict):
                fill_price = order.get('avg_fill_price')
            
            if fill_price is None:
                # Try to get from limit_price if available
                if hasattr(order, 'limit_price'):
                    fill_price = order.limit_price
                elif isinstance(order, dict):
                    fill_price = order.get('limit_price')
            
            # Get filled quantity
            filled_qty = 0.0
            if hasattr(order, 'executed_size'):
                filled_qty = float(order.executed_size)
            elif hasattr(order, 'filled_qty'):
                filled_qty = float(order.filled_qty)
            elif isinstance(order, dict):
                filled_qty = float(order.get('executed_size', order.get('filled_qty', 0)))
            
            # Get trade time (use current time if not available)
            trade_time = None
            if hasattr(order, 'fill_time'):
                trade_time = order.fill_time
            elif isinstance(order, dict):
                trade_time = order.get('fill_time')
            
            # Convert to JoinQuant format
            trade_record = {
                'security': symbol,
                'price': float(fill_price) if fill_price else 0.0,
                'amount': filled_qty,
                'time': trade_time,
                'order_id': order_id,
            }
            
            trades[order_id] = trade_record
    
    return trades

