"""
Tests for WebSocket client.
"""

import pytest
import json
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from engine.python_sdk.websocket_client import (
    WebSocketClient,
    ConnectionState,
    initialize_websocket_client,
    get_websocket_client,
    shutdown_websocket_client,
)
from engine.python_sdk.exceptions import WebSocketConnectionError, WebSocketSubscriptionError
from engine.python_sdk.websocket_cache import get_websocket_cache, set_websocket_cache, WebSocketCache


class TestWebSocketClient:
    """Test WebSocket client."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        client = WebSocketClient(
            symbols=["BTCUSDT"],
            resolutions=["1m"]
        )
        
        assert client.symbols == ["BTCUSDT"]
        assert client.resolutions == ["1m"]
        assert client.get_state() == ConnectionState.DISCONNECTED
    
    def test_state_management(self):
        """Test state management."""
        client = WebSocketClient()
        
        assert client.get_state() == ConnectionState.DISCONNECTED
        
        client.set_state(ConnectionState.CONNECTING)
        assert client.get_state() == ConnectionState.CONNECTING
        
        client.set_state(ConnectionState.CONNECTED)
        assert client.get_state() == ConnectionState.CONNECTED
    
    def test_send_connect_message(self):
        """Test sending CONNECT message."""
        client = WebSocketClient(
            symbols=["BTCUSDT", "ETHUSDT"],
            resolutions=["1m", "5m"],
            csrf_token="test_token",
            market_type="binance-testnet"
        )
        
        # Mock WebSocket
        mock_ws = Mock()
        client._ws = mock_ws
        
        client._send_connect_message()
        
        # Verify send was called
        assert mock_ws.send.called
        
        # Verify message content
        call_args = mock_ws.send.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "CONNECT"
        assert message["symbols"] == ["BTCUSDT", "ETHUSDT"]
        assert message["resolutions"] == ["1m", "5m"]
        assert message["csrf_token"] == "test_token"
        assert message["market_type"] == "binance-testnet"
    
    def test_handle_market_data(self):
        """Test handling market data."""
        # Set up cache
        cache = WebSocketCache()
        set_websocket_cache(cache)
        
        client = WebSocketClient()
        client._cache = cache
        
        # Simulate market data message
        data = {
            "type": "BAR",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "open_time": 1000,
            "close_time": 2000,
            "open": "100.0",
            "high": "110.0",
            "low": "90.0",
            "close": "105.0",
            "volume": "1000.0",
        }
        
        client._handle_market_data(data)
        
        # Verify data was cached
        bars = cache.get_bars("BTCUSDT", "1h")
        assert len(bars) == 1
        assert bars[0]["close"] == "105.0"
    
    def test_handle_connected_message(self):
        """Test handling CONNECTED message."""
        client = WebSocketClient()
        
        data = {"type": "CONNECTED"}
        client._on_message(None, json.dumps(data))
        
        assert client.get_state() == ConnectionState.CONNECTED
    
    def test_handle_error_message(self):
        """Test handling error message."""
        client = WebSocketClient()
        
        data = {
            "type": "ERROR",
            "message": "Subscription failed"
        }
        
        # Error message should set error state and log, but not raise
        client._on_message(None, json.dumps(data))
        
        assert client.get_state() == ConnectionState.ERROR
        assert client.get_last_error() == "Subscription failed"
    
    def test_update_subscription(self):
        """Test updating subscription."""
        client = WebSocketClient(
            symbols=["BTCUSDT"],
            resolutions=["1m"]
        )
        
        # Mock WebSocket
        mock_ws = Mock()
        client._ws = mock_ws
        client.set_state(ConnectionState.CONNECTED)
        
        client.update_subscription(
            symbols=["ETHUSDT"],
            resolutions=["5m"]
        )
        
        assert client.symbols == ["ETHUSDT"]
        assert client.resolutions == ["5m"]
        assert mock_ws.send.called  # Should send new CONNECT message
    
    @patch('engine.python_sdk.websocket_client.websocket.WebSocketApp')
    def test_connect(self, mock_ws_app):
        """Test connecting to WebSocket."""
        client = WebSocketClient(
            symbols=["BTCUSDT"],
            resolutions=["1m"]
        )
        
        mock_ws_instance = Mock()
        mock_ws_app.return_value = mock_ws_instance
        
        client.connect()
        
        # Verify WebSocketApp was created
        mock_ws_app.assert_called_once()
        
        # Verify state changed
        assert client.get_state() == ConnectionState.CONNECTING
    
    def test_disconnect(self):
        """Test disconnecting from WebSocket."""
        client = WebSocketClient()
        
        mock_ws = Mock()
        client._ws = mock_ws
        client.set_state(ConnectionState.CONNECTED)
        client._should_reconnect = True
        
        client.disconnect()
        
        # Verify WebSocket was closed
        mock_ws.close.assert_called_once()
        
        # Verify reconnect is disabled
        assert not client._should_reconnect
        
        # Verify state changed
        assert client.get_state() == ConnectionState.DISCONNECTED


class TestWebSocketClientGlobal:
    """Test global WebSocket client functions."""
    
    def test_initialize_and_get_client(self):
        """Test initializing and getting global client."""
        # Clean up first
        shutdown_websocket_client()
        
        client = initialize_websocket_client(
            symbols=["BTCUSDT"],
            resolutions=["1m"]
        )
        
        assert client is not None
        
        retrieved = get_websocket_client()
        assert retrieved is client
        
        # Clean up
        shutdown_websocket_client()
    
    def test_shutdown_client(self):
        """Test shutting down global client."""
        client = initialize_websocket_client(
            symbols=["BTCUSDT"],
            resolutions=["1m"]
        )
        
        shutdown_websocket_client()
        
        retrieved = get_websocket_client()
        assert retrieved is None

