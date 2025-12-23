"""
Context-based data adapter implementation.

This adapter provides data access from the strategy execution context,
which contains market data from ExecRequest.
"""

from typing import List, Dict, Any, Optional
from .data_adapter import DataAdapter


class ContextDataAdapter(DataAdapter):
    """
    Data adapter that retrieves data from the strategy execution context.
    
    This adapter is used by the strategy execution engine to provide
    data access to SDK methods during strategy execution.
    """
    
    def __init__(self, context: Any):
        """
        Initialize adapter with context.
        
        Args:
            context: Strategy execution context object
        """
        self._context = context
    
    def get_history(self, symbol: str, count: int, timeframe: str) -> List[Any]:
        """
        Get historical bar data from context.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            count: Number of bars to retrieve
            timeframe: Time resolution (e.g., '1h', '1d')
        
        Returns:
            List of Bar objects, ordered from oldest to newest
        """
        # Use context.history method if available
        if hasattr(self._context, 'history'):
            return self._context.history(symbol, count, timeframe)
        
        # Fallback: extract from market_data_context
        return self._extract_bars_from_context(symbol, count, timeframe)
    
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

