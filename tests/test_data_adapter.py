"""
Tests for data adapter interface and implementation.
"""

import pytest
from engine.python_sdk.data_adapter import (
    DataAdapter,
    register_data_adapter,
    get_data_adapter,
    clear_data_adapter,
)
from engine.python_sdk.context_data_adapter import ContextDataAdapter
from engine.context import Context, Account


class TestDataAdapter:
    """Test data adapter interface and registration."""
    
    def test_register_and_get_adapter(self):
        """Test registering and getting data adapter."""
        # Create a mock adapter
        class MockAdapter(DataAdapter):
            def get_history(self, symbol, count, timeframe):
                return []
            
            def get_all_symbols(self):
                return ['BTCUSDT', 'ETHUSDT']
            
            def get_completed_orders(self):
                return []
            
            def get_market_data_context(self):
                return []
        
        adapter = MockAdapter()
        
        # Register adapter
        register_data_adapter(adapter)
        
        # Get adapter
        retrieved = get_data_adapter()
        assert retrieved is adapter
        
        # Clear adapter
        clear_data_adapter()
        
        # Verify adapter is cleared
        with pytest.raises(RuntimeError, match="Data adapter not registered"):
            get_data_adapter()
    
    def test_context_data_adapter(self):
        """Test ContextDataAdapter implementation."""
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
            ]
        }]
        
        context = Context(
            account=account,
            market_data_context=market_data,
            incomplete_orders=[],
            completed_orders=[],
            strategy_params={},
            exec_id="test",
            exchange="binance",
        )
        
        adapter = ContextDataAdapter(context)
        
        # Test get_history
        bars = adapter.get_history("BTCUSDT", 1, "1h")
        assert len(bars) == 1
        
        # Test get_all_symbols
        symbols = adapter.get_all_symbols()
        assert "BTCUSDT" in symbols
        
        # Test get_market_data_context
        market_context = adapter.get_market_data_context()
        assert len(market_context) == 1
        assert market_context[0]["symbol"] == "BTCUSDT"
        
        # Test get_completed_orders
        orders = adapter.get_completed_orders()
        assert isinstance(orders, list)
    
    def test_adapter_not_registered_error(self):
        """Test error when adapter is not registered."""
        clear_data_adapter()  # Ensure no adapter is registered
        
        with pytest.raises(RuntimeError, match="Data adapter not registered"):
            get_data_adapter()
    
    def test_adapter_thread_safety(self):
        """Test that adapter is thread-local."""
        import threading
        
        class MockAdapter1(DataAdapter):
            def get_history(self, symbol, count, timeframe):
                return []
            
            def get_all_symbols(self):
                return ['ADAPTER1']
            
            def get_completed_orders(self):
                return []
            
            def get_market_data_context(self):
                return []
        
        class MockAdapter2(DataAdapter):
            def get_history(self, symbol, count, timeframe):
                return []
            
            def get_all_symbols(self):
                return ['ADAPTER2']
            
            def get_completed_orders(self):
                return []
            
            def get_market_data_context(self):
                return []
        
        adapter1 = MockAdapter1()
        adapter2 = MockAdapter2()
        
        results = {}
        
        def thread1():
            register_data_adapter(adapter1)
            retrieved = get_data_adapter()
            results['thread1'] = retrieved.get_all_symbols()
        
        def thread2():
            register_data_adapter(adapter2)
            retrieved = get_data_adapter()
            results['thread2'] = retrieved.get_all_symbols()
        
        t1 = threading.Thread(target=thread1)
        t2 = threading.Thread(target=thread2)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Each thread should have its own adapter
        assert results['thread1'] == ['ADAPTER1']
        assert results['thread2'] == ['ADAPTER2']
        
        # Clean up
        clear_data_adapter()

