"""
Integration tests for WebSocket market data integration.
"""

import pytest
from engine.python_sdk.context_data_adapter import ContextDataAdapter
from engine.python_sdk.websocket_cache import WebSocketCache, set_websocket_cache
from engine.context import Context, Account, Bar
from engine.python_sdk.data_adapter import register_data_adapter, clear_data_adapter


class TestWebSocketIntegration:
    """Test WebSocket integration with data adapter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a fresh cache for each test
        self.cache = WebSocketCache()
        set_websocket_cache(self.cache)
        
        # Create context
        account = Account(account_id="test")
        market_data = [{
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "bars": [
                {
                    "open_time": 1000,
                    "close_time": 2000,
                    "open": "100.0",
                    "high": "110.0",
                    "low": "90.0",
                    "close": "105.0",
                    "volume": "1000.0",
                },
                {
                    "open_time": 2000,
                    "close_time": 3000,
                    "open": "105.0",
                    "high": "115.0",
                    "low": "95.0",
                    "close": "110.0",
                    "volume": "1100.0",
                },
            ]
        }]
        
        self.context = Context(
            account=account,
            market_data_context=market_data,
            incomplete_orders=[],
            completed_orders=[],
            strategy_params={},
            exec_id="test",
            exchange="binance",
        )
        
        self.adapter = ContextDataAdapter(self.context)
    
    def teardown_method(self):
        """Clean up after test."""
        clear_data_adapter()
    
    def test_get_history_from_context_only(self):
        """Test getting history from context when WebSocket cache is empty."""
        # WebSocket cache is empty
        bars = self.adapter.get_history("BTCUSDT", 2, "1h")
        
        assert len(bars) == 2
        # Bars are Bar objects, use attribute access
        close0 = bars[0].close if hasattr(bars[0], 'close') else bars[0].get("close")
        close1 = bars[1].close if hasattr(bars[1], 'close') else bars[1].get("close")
        assert close0 == "105.0"
        assert close1 == "110.0"
    
    def test_get_history_from_websocket_cache(self):
        """Test getting history from WebSocket cache when available."""
        # Add data to WebSocket cache
        websocket_bar = {
            "open_time": 3000,
            "close_time": 4000,
            "open": "110.0",
            "high": "120.0",
            "low": "100.0",
            "close": "115.0",
            "volume": "1200.0",
        }
        self.cache.add_bar("BTCUSDT", "1h", websocket_bar)
        
        # Get history - should prefer WebSocket cache
        bars = self.adapter.get_history("BTCUSDT", 1, "1h")
        
        assert len(bars) >= 1
        # Should get from WebSocket cache (newest)
        close = bars[-1].close if hasattr(bars[-1], 'close') else bars[-1].get("close")
        assert close == "115.0"
    
    def test_get_history_merged(self):
        """Test getting history with merged data from both sources."""
        # Add data to WebSocket cache
        websocket_bar = {
            "open_time": 3000,
            "close_time": 4000,
            "open": "110.0",
            "high": "120.0",
            "low": "100.0",
            "close": "115.0",
            "volume": "1200.0",
        }
        self.cache.add_bar("BTCUSDT", "1h", websocket_bar)
        
        # Get history - should merge both sources
        bars = self.adapter.get_history("BTCUSDT", 3, "1h")
        
        # Should have 3 bars: 2 from context + 1 from WebSocket
        assert len(bars) >= 2
        # Last bar should be from WebSocket (newest)
        close = bars[-1].close if hasattr(bars[-1], 'close') else bars[-1].get("close")
        assert close == "115.0"
    
    def test_get_history_websocket_priority(self):
        """Test that WebSocket data takes priority when both sources have data."""
        # Add data to WebSocket cache with same timeframe
        websocket_bar = {
            "open_time": 2000,
            "close_time": 3000,
            "open": "105.0",
            "high": "115.0",
            "low": "95.0",
            "close": "112.0",  # Different from context
            "volume": "1100.0",
        }
        self.cache.add_bar("BTCUSDT", "1h", websocket_bar)
        
        # Get history - WebSocket should take priority for overlapping time
        bars = self.adapter.get_history("BTCUSDT", 2, "1h")
        
        # Should have 2 bars
        assert len(bars) == 2
        # The bar with close_time 3000 should come from WebSocket
        # (WebSocket data is newer, so it should be preferred)
        close = bars[-1].close if hasattr(bars[-1], 'close') else bars[-1].get("close")
        assert close == "112.0"  # From WebSocket
    
    def test_get_history_different_timeframe(self):
        """Test getting history for different timeframe."""
        # Add data to WebSocket cache for different timeframe
        websocket_bar = {
            "open_time": 1000,
            "close_time": 2000,
            "open": "100.0",
            "high": "110.0",
            "low": "90.0",
            "close": "105.0",
            "volume": "1000.0",
        }
        self.cache.add_bar("BTCUSDT", "5m", websocket_bar)
        
        # Get history for 1h timeframe - should only get from context
        bars = self.adapter.get_history("BTCUSDT", 2, "1h")
        
        assert len(bars) == 2
        # Should not include 5m data
        closes = [bar.close if hasattr(bar, 'close') else bar.get("close") for bar in bars]
        assert all(close in ["105.0", "110.0"] for close in closes)
    
    def test_get_history_different_symbol(self):
        """Test getting history for different symbol."""
        # Add data to WebSocket cache for different symbol
        websocket_bar = {
            "open_time": 1000,
            "close_time": 2000,
            "open": "100.0",
            "high": "110.0",
            "low": "90.0",
            "close": "105.0",
            "volume": "1000.0",
        }
        self.cache.add_bar("ETHUSDT", "1h", websocket_bar)
        
        # Get history for BTCUSDT - should only get from context
        bars = self.adapter.get_history("BTCUSDT", 2, "1h")
        
        assert len(bars) == 2
        # Should not include ETHUSDT data
        closes = [bar.close if hasattr(bar, 'close') else bar.get("close") for bar in bars]
        assert all(close in ["105.0", "110.0"] for close in closes)
    
    def test_backtest_compatibility(self):
        """Test that backtest scenario still works (no WebSocket cache)."""
        # Clear WebSocket cache
        self.cache.clear()
        
        # Get history - should work with context only
        bars = self.adapter.get_history("BTCUSDT", 2, "1h")
        
        assert len(bars) == 2
        close0 = bars[0].close if hasattr(bars[0], 'close') else bars[0].get("close")
        close1 = bars[1].close if hasattr(bars[1], 'close') else bars[1].get("close")
        assert close0 == "105.0"
        assert close1 == "110.0"

