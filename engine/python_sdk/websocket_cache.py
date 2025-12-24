"""
WebSocket market data cache.

This module provides a thread-safe cache for storing real-time market data
received from WebSocket connections.
"""

import threading
from typing import List, Dict, Optional, Any
from collections import deque
from datetime import datetime


class WebSocketCache:
    """
    Thread-safe cache for WebSocket market data.
    
    Data is organized by (symbol, timeframe) keys and stored as a deque
    to efficiently manage size limits.
    """
    
    def __init__(self, max_bars_per_symbol: int = 1000):
        """
        Initialize the cache.
        
        Args:
            max_bars_per_symbol: Maximum number of bars to cache per (symbol, timeframe) pair
        """
        self._max_bars = max_bars_per_symbol
        self._cache: Dict[tuple, deque] = {}  # (symbol, timeframe) -> deque of bars
        self._lock = threading.RLock()
        self._last_update: Dict[tuple, int] = {}  # (symbol, timeframe) -> last update timestamp
    
    def add_bar(self, symbol: str, timeframe: str, bar: Dict[str, Any]) -> None:
        """
        Add a new bar to the cache.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Time resolution (e.g., '1h', '1m')
            bar: Bar data dictionary with keys: open_time, close_time, open, high, low, close, volume
        """
        key = (symbol, timeframe)
        
        with self._lock:
            if key not in self._cache:
                self._cache[key] = deque(maxlen=self._max_bars)
            
            # Convert bar dict to a more structured format if needed
            # Store as dict for now, can be converted to Bar object later
            self._cache[key].append(bar)
            
            # Update last update timestamp
            close_time = bar.get('close_time', 0)
            if isinstance(close_time, str):
                try:
                    close_time = int(close_time)
                except ValueError:
                    close_time = 0
            self._last_update[key] = close_time
    
    def get_bars(self, symbol: str, timeframe: str, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get bars from cache.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Time resolution (e.g., '1h', '1m')
            count: Number of bars to retrieve (None means all)
        
        Returns:
            List of bar dictionaries, ordered from oldest to newest
        """
        key = (symbol, timeframe)
        
        with self._lock:
            if key not in self._cache:
                return []
            
            bars = list(self._cache[key])
            
            if count is not None and count > 0:
                # Return the last count bars
                bars = bars[-count:] if len(bars) > count else bars
            
            return bars
    
    def get_latest_bar(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest bar for a symbol and timeframe.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Time resolution (e.g., '1h', '1m')
        
        Returns:
            Latest bar dictionary, or None if not available
        """
        key = (symbol, timeframe)
        
        with self._lock:
            if key not in self._cache or len(self._cache[key]) == 0:
                return None
            
            return self._cache[key][-1]
    
    def get_last_update_time(self, symbol: str, timeframe: str) -> Optional[int]:
        """
        Get the last update timestamp for a symbol and timeframe.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Time resolution (e.g., '1h', '1m')
        
        Returns:
            Last update timestamp (close_time of latest bar), or None if not available
        """
        key = (symbol, timeframe)
        
        with self._lock:
            return self._last_update.get(key)
    
    def clear(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> None:
        """
        Clear cache for a specific symbol/timeframe or all.
        
        Args:
            symbol: If provided, only clear this symbol (and optionally timeframe)
            timeframe: If provided with symbol, only clear this specific (symbol, timeframe) pair
        """
        with self._lock:
            if symbol is None:
                # Clear all
                self._cache.clear()
                self._last_update.clear()
            elif timeframe is None:
                # Clear all timeframes for this symbol
                keys_to_remove = [k for k in self._cache.keys() if k[0] == symbol]
                for key in keys_to_remove:
                    del self._cache[key]
                    if key in self._last_update:
                        del self._last_update[key]
            else:
                # Clear specific (symbol, timeframe) pair
                key = (symbol, timeframe)
                if key in self._cache:
                    del self._cache[key]
                if key in self._last_update:
                    del self._last_update[key]
    
    def get_cached_symbols(self) -> List[tuple]:
        """
        Get list of (symbol, timeframe) pairs that have cached data.
        
        Returns:
            List of (symbol, timeframe) tuples
        """
        with self._lock:
            return list(self._cache.keys())
    
    def get_cache_size(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> int:
        """
        Get the number of bars cached for a symbol/timeframe or total.
        
        Args:
            symbol: If provided, only count this symbol (and optionally timeframe)
            timeframe: If provided with symbol, only count this specific (symbol, timeframe) pair
        
        Returns:
            Number of bars cached
        """
        with self._lock:
            if symbol is None:
                # Total size
                return sum(len(bars) for bars in self._cache.values())
            elif timeframe is None:
                # Size for all timeframes of this symbol
                return sum(
                    len(bars) for key, bars in self._cache.items()
                    if key[0] == symbol
                )
            else:
                # Size for specific (symbol, timeframe) pair
                key = (symbol, timeframe)
                return len(self._cache.get(key, []))


# Global cache instance
_global_cache: Optional[WebSocketCache] = None
_cache_lock = threading.Lock()


def get_websocket_cache() -> WebSocketCache:
    """
    Get the global WebSocket cache instance.
    
    Returns:
        Global WebSocketCache instance
    """
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = WebSocketCache()
    
    return _global_cache


def set_websocket_cache(cache: WebSocketCache) -> None:
    """
    Set the global WebSocket cache instance (mainly for testing).
    
    Args:
        cache: WebSocketCache instance to use
    """
    global _global_cache
    
    with _cache_lock:
        _global_cache = cache

