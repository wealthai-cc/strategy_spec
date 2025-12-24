#!/usr/bin/env python3
"""
Simple test script for WebSocket functionality.
This can be run without pytest to verify basic functionality.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cache():
    """Test WebSocket cache."""
    print("Testing WebSocket cache...")
    
    # Direct import to avoid __init__.py dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "websocket_cache",
        "engine/python_sdk/websocket_cache.py"
    )
    websocket_cache = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(websocket_cache)
    WebSocketCache = websocket_cache.WebSocketCache
    get_websocket_cache = websocket_cache.get_websocket_cache
    
    # Test cache creation
    cache = WebSocketCache(max_bars_per_symbol=100)
    assert cache.get_cache_size() == 0
    print("✓ Cache creation works")
    
    # Test adding bar
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
    assert cache.get_cache_size() == 1
    print("✓ Adding bar works")
    
    # Test getting bars
    bars = cache.get_bars("BTCUSDT", "1h")
    assert len(bars) == 1
    assert bars[0]["close"] == "105.0"
    print("✓ Getting bars works")
    
    # Test global cache
    global_cache = get_websocket_cache()
    assert global_cache is not None
    print("✓ Global cache works")
    
    print("Cache tests passed!\n")


def test_client():
    """Test WebSocket client (without actual connection)."""
    print("Testing WebSocket client...")
    
    # Direct import to avoid __init__.py dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "websocket_client",
        "engine/python_sdk/websocket_client.py"
    )
    websocket_client = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(websocket_client)
    WebSocketClient = websocket_client.WebSocketClient
    ConnectionState = websocket_client.ConnectionState
    
    # Test client initialization
    client = WebSocketClient(
        symbols=["BTCUSDT"],
        resolutions=["1m"]
    )
    assert client.symbols == ["BTCUSDT"]
    assert client.resolutions == ["1m"]
    assert client.get_state() == ConnectionState.DISCONNECTED
    print("✓ Client initialization works")
    
    # Test state management
    client.set_state(ConnectionState.CONNECTING)
    assert client.get_state() == ConnectionState.CONNECTING
    print("✓ State management works")
    
    # Test CONNECT message preparation
    from unittest.mock import Mock
    mock_ws = Mock()
    client._ws = mock_ws
    client._send_connect_message()
    assert mock_ws.send.called
    print("✓ CONNECT message sending works")
    
    print("Client tests passed!\n")


def test_adapter_integration():
    """Test data adapter integration."""
    print("Testing data adapter integration...")
    
    # Direct imports to avoid __init__.py dependencies
    import importlib.util
    
    # Import websocket_cache
    spec = importlib.util.spec_from_file_location(
        "websocket_cache",
        "engine/python_sdk/websocket_cache.py"
    )
    websocket_cache = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(websocket_cache)
    WebSocketCache = websocket_cache.WebSocketCache
    set_websocket_cache = websocket_cache.set_websocket_cache
    
    # Import context_data_adapter
    spec = importlib.util.spec_from_file_location(
        "context_data_adapter",
        "engine/python_sdk/context_data_adapter.py"
    )
    context_data_adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(context_data_adapter)
    ContextDataAdapter = context_data_adapter.ContextDataAdapter
    
    from engine.context import Context, Account
    
    # Set up cache
    cache = WebSocketCache()
    set_websocket_cache(cache)
    
    # Add WebSocket data
    websocket_bar = {
        "open_time": 3000,
        "close_time": 4000,
        "open": "110.0",
        "high": "120.0",
        "low": "100.0",
        "close": "115.0",
        "volume": "1200.0",
    }
    cache.add_bar("BTCUSDT", "1h", websocket_bar)
    
    # Create context with market data
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
    
    # Test getting history - should prefer WebSocket cache
    bars = adapter.get_history("BTCUSDT", 1, "1h")
    assert len(bars) >= 1
    print("✓ Adapter integration works (WebSocket priority)")
    
    # Test getting history from context only
    cache.clear()
    bars = adapter.get_history("BTCUSDT", 1, "1h")
    assert len(bars) == 1
    assert bars[0]["close"] == "105.0"
    print("✓ Adapter integration works (Context fallback)")
    
    print("Adapter integration tests passed!\n")


def test_manager():
    """Test WebSocket manager."""
    print("Testing WebSocket manager...")
    
    # Direct import to avoid __init__.py dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "websocket_manager",
        "engine/python_sdk/websocket_manager.py"
    )
    websocket_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(websocket_manager)
    WebSocketManager = websocket_manager.WebSocketManager
    
    manager = WebSocketManager()
    assert manager._client is None
    print("✓ Manager initialization works")
    
    # Test configuration
    manager.configure(
        symbols=["BTCUSDT"],
        resolutions=["1m"]
    )
    assert manager._config['symbols'] == ["BTCUSDT"]
    print("✓ Manager configuration works")
    
    # Test status (no client)
    status = manager.get_status()
    assert status['state'] == 'disconnected'
    print("✓ Manager status works")
    
    print("Manager tests passed!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("WebSocket Functionality Tests")
    print("=" * 60)
    print()
    
    try:
        test_cache()
        test_client()
        test_adapter_integration()
        test_manager()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

