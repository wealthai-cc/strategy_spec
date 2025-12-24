"""
Tests for WebSocket cache.
"""

import pytest
from engine.python_sdk.websocket_cache import WebSocketCache, get_websocket_cache, set_websocket_cache


def test_cache_creation():
    """Test cache creation."""
    cache = WebSocketCache(max_bars_per_symbol=100)
    assert cache is not None
    assert cache.get_cache_size() == 0


def test_add_and_get_bar():
    """Test adding and getting bars."""
    cache = WebSocketCache()
    
    bar = {
        "open_time": 1000,
        "close_time": 2000,
        "open": "100.0",
        "high": "110.0",
        "low": "90.0",
        "close": "105.0",
        "volume": "1000.0",
    }
    
    cache.add_bar("BTCUSDT", "1h", bar)
    
    bars = cache.get_bars("BTCUSDT", "1h")
    assert len(bars) == 1
    assert bars[0]["close"] == "105.0"
    
    latest = cache.get_latest_bar("BTCUSDT", "1h")
    assert latest is not None
    assert latest["close"] == "105.0"


def test_cache_size_limit():
    """Test cache size limit."""
    cache = WebSocketCache(max_bars_per_symbol=5)
    
    for i in range(10):
        bar = {
            "open_time": i * 1000,
            "close_time": (i + 1) * 1000,
            "open": str(100 + i),
            "high": str(110 + i),
            "low": str(90 + i),
            "close": str(105 + i),
            "volume": str(1000 + i),
        }
        cache.add_bar("BTCUSDT", "1h", bar)
    
    bars = cache.get_bars("BTCUSDT", "1h")
    assert len(bars) == 5  # Should be limited to 5
    # With maxlen=5, deque keeps the last 5 items (indices 5-9)
    # So oldest is index 5 (close="110"), newest is index 9 (close="114")
    assert bars[0]["close"] == "110"  # Oldest should be 110 (6th bar, index 5)
    assert bars[-1]["close"] == "114"  # Newest should be 114 (10th bar, index 9)


def test_get_bars_with_count():
    """Test getting bars with count limit."""
    cache = WebSocketCache()
    
    for i in range(10):
        bar = {
            "open_time": i * 1000,
            "close_time": (i + 1) * 1000,
            "open": str(100 + i),
            "high": str(110 + i),
            "low": str(90 + i),
            "close": str(105 + i),
            "volume": str(1000 + i),
        }
        cache.add_bar("BTCUSDT", "1h", bar)
    
    bars = cache.get_bars("BTCUSDT", "1h", count=3)
    assert len(bars) == 3
    # Should get last 3 bars (indices 7-9)
    assert bars[-1]["close"] == "114"  # Should get last 3 bars (indices 7-9)


def test_clear_cache():
    """Test clearing cache."""
    cache = WebSocketCache()
    
    bar = {
        "open_time": 1000,
        "close_time": 2000,
        "open": "100.0",
        "high": "110.0",
        "low": "90.0",
        "close": "105.0",
        "volume": "1000.0",
    }
    
    cache.add_bar("BTCUSDT", "1h", bar)
    assert cache.get_cache_size() > 0
    
    cache.clear("BTCUSDT", "1h")
    assert cache.get_cache_size("BTCUSDT", "1h") == 0


def test_global_cache():
    """Test global cache instance."""
    cache1 = get_websocket_cache()
    cache2 = get_websocket_cache()
    
    assert cache1 is cache2  # Should be the same instance
    
    # Test setting custom cache
    custom_cache = WebSocketCache()
    set_websocket_cache(custom_cache)
    
    cache3 = get_websocket_cache()
    assert cache3 is custom_cache

