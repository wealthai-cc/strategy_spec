"""
Data adapter interface for wealthdata SDK methods.

This module provides the data adapter interface that allows SDK methods
to access data independently of the strategy execution engine context.
"""

import threading
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import pandas as pd


class DataAdapter(ABC):
    """
    Data adapter interface for accessing market data and related information.
    
    This interface allows SDK methods to access data without directly
    depending on the strategy execution engine context. Different
    implementations can provide data from different sources (backtest,
    mock trading, real trading).
    """
    
    @abstractmethod
    def get_history(self, symbol: str, count: int, timeframe: str) -> List[Any]:
        """
        Get historical bar data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            count: Number of bars to retrieve
            timeframe: Time resolution (e.g., '1h', '1d')
        
        Returns:
            List of Bar objects, ordered from oldest to newest
        """
        pass
    
    @abstractmethod
    def get_all_symbols(self) -> List[str]:
        """
        Get all available trading pair symbols.
        
        Returns:
            List of trading pair symbols
        """
        pass
    
    @abstractmethod
    def get_completed_orders(self) -> List[Any]:
        """
        Get completed orders.
        
        Returns:
            List of completed order objects
        """
        pass
    
    @abstractmethod
    def get_market_data_context(self) -> List[Dict[str, Any]]:
        """
        Get market data context (raw market data from ExecRequest).
        
        Returns:
            List of market data context dictionaries
        """
        pass


# Thread-local storage for data adapter
_adapter_local = threading.local()


def register_data_adapter(adapter: DataAdapter) -> None:
    """
    Register a data adapter for the current thread.
    
    Args:
        adapter: Data adapter instance to register
    
    This function is called by the strategy execution engine before
    executing strategy functions. The adapter is stored in thread-local
    storage to support concurrent strategy execution.
    """
    _adapter_local.adapter = adapter


def get_data_adapter() -> DataAdapter:
    """
    Get the data adapter for the current thread.
    
    Returns:
        Data adapter instance for the current thread
    
    Raises:
        RuntimeError: If no adapter is registered for the current thread
    """
    adapter = getattr(_adapter_local, 'adapter', None)
    if adapter is None:
        raise RuntimeError(
            "Data adapter not registered. "
            "The strategy execution engine should register a data adapter "
            "before executing strategy functions."
        )
    return adapter


def clear_data_adapter() -> None:
    """
    Clear the data adapter for the current thread.
    
    This function is called by the strategy execution engine after
    executing strategy functions to prevent memory leaks.
    """
    if hasattr(_adapter_local, 'adapter'):
        delattr(_adapter_local, 'adapter')

