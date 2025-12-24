"""
Context-based data adapter implementation.

This adapter provides data access from the strategy execution context,
which contains market data from ExecRequest. It also supports reading
from WebSocket cache for real-time data.
"""

from typing import List, Dict, Any, Optional
from .data_adapter import DataAdapter


class ContextDataAdapter(DataAdapter):
    """
    Data adapter that retrieves data from the strategy execution context.
    
    This adapter is used by the strategy execution engine to provide
    data access to SDK methods during strategy execution.
    
    It implements a hybrid data source approach:
    1. First tries to get data from WebSocket cache (real-time data)
    2. Falls back to Context data (from ExecRequest) if WebSocket cache is empty
    3. Can merge data from both sources if needed
    """
    
    def __init__(self, context: Any):
        """
        Initialize adapter with context.
        
        Args:
            context: Strategy execution context object
        """
        self._context = context
        self._websocket_cache = None
        
        # Lazy import to avoid circular dependencies
        try:
            from .websocket_cache import get_websocket_cache
            self._websocket_cache = get_websocket_cache()
        except ImportError:
            # WebSocket cache not available, will only use context
            pass
    
    def get_history(self, symbol: str, count: int, timeframe: str) -> List[Any]:
        """
        Get historical bar data from hybrid data sources.
        
        Priority:
        1. WebSocket cache (real-time data)
        2. Context data (from ExecRequest, for backtest)
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            count: Number of bars to retrieve
            timeframe: Time resolution (e.g., '1h', '1d')
        
        Returns:
            List of Bar objects, ordered from oldest to newest
        """
        # Try WebSocket cache first (real-time data)
        websocket_bars = self._get_bars_from_websocket_cache(symbol, count, timeframe)
        
        if websocket_bars and len(websocket_bars) >= count:
            # We have enough data from WebSocket cache
            return websocket_bars
        
        # Get data from context (backtest scenario or supplement)
        context_bars = self._get_bars_from_context(symbol, count, timeframe)
        
        if not websocket_bars:
            # No WebSocket data, return context data only
            return context_bars
        
        # Merge: WebSocket data (real-time) + Context data (historical)
        # WebSocket data is more recent, so it should come after context data
        # But we want oldest first, so: context (old) + websocket (new)
        merged_bars = context_bars + websocket_bars
        
        # Remove duplicates based on close_time, keeping the latest
        seen_times = set()
        unique_bars = []
        for bar in reversed(merged_bars):  # Process from newest to oldest
            close_time = self._get_bar_close_time(bar)
            if close_time not in seen_times:
                seen_times.add(close_time)
                unique_bars.append(bar)
        
        # Return in chronological order (oldest first)
        unique_bars.reverse()
        
        # Return the last count bars
        return unique_bars[-count:] if len(unique_bars) > count else unique_bars
    
    def _get_bars_from_websocket_cache(self, symbol: str, count: int, timeframe: str) -> List[Any]:
        """Get bars from WebSocket cache."""
        if self._websocket_cache is None:
            return []
        
        try:
            cache_bars = self._websocket_cache.get_bars(symbol, timeframe, count)
            if not cache_bars:
                return []
            
            # Convert dict to Bar object if needed
            return [self._dict_to_bar(bar) for bar in cache_bars]
        except Exception as e:
            # If WebSocket cache fails, fall back to context
            import logging
            logging.getLogger(__name__).debug(f"WebSocket cache error: {e}, falling back to context")
            return []
    
    def _get_bars_from_context(self, symbol: str, count: int, timeframe: str) -> List[Any]:
        """Get bars from context."""
        # Use context.history method if available
        if hasattr(self._context, 'history'):
            return self._context.history(symbol, count, timeframe)
        
        # Fallback: extract from market_data_context
        return self._extract_bars_from_context(symbol, count, timeframe)
    
    def _get_bar_close_time(self, bar: Any) -> int:
        """Extract close_time from a bar (dict or object)."""
        if isinstance(bar, dict):
            return bar.get('close_time', 0)
        elif hasattr(bar, 'close_time'):
            return getattr(bar, 'close_time', 0)
        else:
            return 0
    
    def _dict_to_bar(self, bar_dict: Dict[str, Any]) -> Any:
        """
        Convert a bar dictionary to Bar object.
        
        If context uses Bar objects, try to create one. Otherwise return dict.
        """
        # Check if context uses Bar objects by looking at context's bar structure
        if hasattr(self._context, 'current_bar') and self._context.current_bar is not None:
            # Context uses Bar objects, try to create one
            try:
                from engine.context.context import Bar
                return Bar(
                    open_time=int(bar_dict.get('open_time', 0)),
                    close_time=int(bar_dict.get('close_time', 0)),
                    open=str(bar_dict.get('open', '0')),
                    high=str(bar_dict.get('high', '0')),
                    low=str(bar_dict.get('low', '0')),
                    close=str(bar_dict.get('close', '0')),
                    volume=str(bar_dict.get('volume', '0')),
                )
            except (ImportError, AttributeError, ValueError):
                # Bar class not available or conversion failed, return dict
                return bar_dict
        else:
            # Context uses dicts, return dict
            return bar_dict
    
    def _extract_bars_from_context(self, symbol: str, count: int, timeframe: str) -> List[Any]:
        """Extract bars from market_data_context."""
        bars = []
        market_data_context = getattr(self._context, '_market_data_context', [])
        
        for market_context in market_data_context:
            if market_context.get('symbol') == symbol:
                context_bars = market_context.get('bars', [])
                # Filter by timeframe if needed
                context_timeframe = market_context.get('timeframe', '1h')
                if context_timeframe == timeframe:
                    # Return the last count bars
                    bars = context_bars[-count:] if len(context_bars) > count else context_bars
                    break
        
        # Convert dict bars to Bar objects if context uses Bar objects
        if bars and hasattr(self._context, 'current_bar') and self._context.current_bar is not None:
            try:
                from engine.context.context import Bar
                converted_bars = []
                for bar_data in bars:
                    if isinstance(bar_data, dict):
                        converted_bars.append(Bar(
                            open_time=int(bar_data.get('open_time', 0)),
                            close_time=int(bar_data.get('close_time', 0)),
                            open=str(bar_data.get('open', '0')),
                            high=str(bar_data.get('high', '0')),
                            low=str(bar_data.get('low', '0')),
                            close=str(bar_data.get('close', '0')),
                            volume=str(bar_data.get('volume', '0')),
                        ))
                    else:
                        converted_bars.append(bar_data)
                return converted_bars
            except (ImportError, AttributeError, ValueError):
                # Conversion failed, return original
                return bars
        
        return bars
    
    def get_all_symbols(self) -> List[str]:
        """
        Get all available trading pair symbols from context.
        
        Returns:
            List of trading pair symbols
        """
        symbols = set()
        market_data_context = getattr(self._context, '_market_data_context', [])
        
        for market_context in market_data_context:
            symbol = market_context.get('symbol')
            if symbol:
                symbols.add(symbol)
        
        return sorted(list(symbols))
    
    def get_completed_orders(self) -> List[Any]:
        """
        Get completed orders from context.
        
        Returns:
            List of completed order objects
        """
        # Get completed orders from context
        completed_orders = getattr(self._context, '_completed_orders', [])
        return completed_orders
    
    def get_incomplete_orders(self) -> List[Any]:
        """
        Get incomplete orders from context.
        
        Returns:
            List of incomplete order objects
        """
        # Get incomplete orders from context
        incomplete_orders = getattr(self._context, '_incomplete_orders', [])
        return incomplete_orders
    
    def get_market_data_context(self) -> List[Dict[str, Any]]:
        """
        Get raw market data context.
        
        Returns:
            List of market data context dictionaries
        """
        return getattr(self._context, '_market_data_context', [])

