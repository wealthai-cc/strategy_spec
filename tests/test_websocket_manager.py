"""
Tests for WebSocket manager.
"""

import pytest
import os
from unittest.mock import patch, Mock
from engine.python_sdk.websocket_manager import (
    WebSocketManager,
    get_websocket_manager,
)
from engine.python_sdk.websocket_client import ConnectionState
from engine.python_sdk.exceptions import WebSocketConnectionError, WebSocketSubscriptionError


class TestWebSocketManager:
    """Test WebSocket manager."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = WebSocketManager()
        assert manager._client is None
        assert manager._config == {}
    
    @patch.dict(os.environ, {
        'WEBSOCKET_ENDPOINT': 'wss://test.example.com:8080/market_data',
        'WEBSOCKET_CSRF_TOKEN': 'test_token',
        'WEBSOCKET_MARKET_TYPE': 'binance',
        'WEBSOCKET_SYMBOLS': 'BTCUSDT,ETHUSDT',
        'WEBSOCKET_RESOLUTIONS': '1m,5m,1h',
    })
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        manager = WebSocketManager()
        config = manager.load_config_from_env()
        
        assert config['endpoint'] == 'wss://test.example.com:8080/market_data'
        assert config['csrf_token'] == 'test_token'
        assert config['market_type'] == 'binance'
        assert config['symbols'] == ['BTCUSDT', 'ETHUSDT']
        assert config['resolutions'] == ['1m', '5m', '1h']
    
    def test_load_config_defaults(self):
        """Test loading configuration with defaults."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            manager = WebSocketManager()
            config = manager.load_config_from_env()
            
            assert config['endpoint'] == 'wss://ws.wealthai.cc:18000/market_data'
            assert config['csrf_token'] == '154c3ceaee6ee63a9fb6aa669873d08aec4655944bce20b6e6c413dc4db0ccd5'
            assert config['market_type'] == 'binance-testnet'
            assert config['symbols'] == []
            assert config['resolutions'] == []
    
    def test_configure(self):
        """Test configuring manager."""
        manager = WebSocketManager()
        
        manager.configure(
            symbols=["BTCUSDT"],
            resolutions=["1m", "5m"]
        )
        
        assert manager._config['symbols'] == ["BTCUSDT"]
        assert manager._config['resolutions'] == ["1m", "5m"]
    
    @patch('engine.python_sdk.websocket_manager.initialize_websocket_client')
    def test_start(self, mock_init):
        """Test starting WebSocket client."""
        manager = WebSocketManager()
        manager.configure(
            symbols=["BTCUSDT"],
            resolutions=["1m"]
        )
        
        mock_client = Mock()
        mock_init.return_value = mock_client
        
        manager.start()
        
        assert manager._client is mock_client
        mock_init.assert_called_once()
    
    @patch('engine.python_sdk.websocket_manager.initialize_websocket_client')
    def test_start_without_config(self, mock_init):
        """Test starting without configuration."""
        manager = WebSocketManager()
        
        # Should not start if no symbols/resolutions
        manager.start()
        
        mock_init.assert_not_called()
    
    def test_stop(self):
        """Test stopping WebSocket client."""
        manager = WebSocketManager()
        mock_client = Mock()
        manager._client = mock_client
        
        manager.stop()
        
        mock_client.disconnect.assert_called_once()
        assert manager._client is None
    
    def test_update_subscription(self):
        """Test updating subscription."""
        manager = WebSocketManager()
        mock_client = Mock()
        manager._client = mock_client
        
        manager.update_subscription(
            symbols=["ETHUSDT"],
            resolutions=["5m"]
        )
        
        mock_client.update_subscription.assert_called_once_with(
            ["ETHUSDT"],
            ["5m"]
        )
        assert manager._config['symbols'] == ["ETHUSDT"]
        assert manager._config['resolutions'] == ["5m"]
    
    def test_update_subscription_no_client(self):
        """Test updating subscription when client is not started."""
        manager = WebSocketManager()
        
        with pytest.raises(WebSocketSubscriptionError, match="WebSocket client not started"):
            manager.update_subscription(
                symbols=["BTCUSDT"],
                resolutions=["1m"]
            )
    
    def test_get_status(self):
        """Test getting connection status."""
        manager = WebSocketManager()
        
        # No client
        status = manager.get_status()
        assert status['state'] == ConnectionState.DISCONNECTED.value
        assert status['last_error'] is None
        
        # With client
        mock_client = Mock()
        mock_client.get_state.return_value = ConnectionState.CONNECTED
        mock_client.get_last_error.return_value = None
        mock_client.symbols = ["BTCUSDT"]
        mock_client.resolutions = ["1m"]
        manager._client = mock_client
        
        status = manager.get_status()
        assert status['state'] == ConnectionState.CONNECTED.value
        assert status['symbols'] == ["BTCUSDT"]
        assert status['resolutions'] == ["1m"]
    
    def test_is_connected(self):
        """Test checking connection status."""
        manager = WebSocketManager()
        
        # No client
        assert not manager.is_connected()
        
        # Client disconnected
        mock_client = Mock()
        mock_client.get_state.return_value = ConnectionState.DISCONNECTED
        manager._client = mock_client
        assert not manager.is_connected()
        
        # Client connected
        mock_client.get_state.return_value = ConnectionState.CONNECTED
        assert manager.is_connected()


class TestWebSocketManagerGlobal:
    """Test global WebSocket manager functions."""
    
    def test_get_manager(self):
        """Test getting global manager."""
        manager1 = get_websocket_manager()
        manager2 = get_websocket_manager()
        
        # Should return the same instance
        assert manager1 is manager2

