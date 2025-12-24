"""
WebSocket manager for configuring and managing WebSocket connections.

This module provides system-level APIs for configuring WebSocket connections
and subscriptions. Strategies don't need to use these APIs directly - they
are used by the strategy management system.
"""

import os
import logging
import threading
from typing import List, Optional, Dict, Any
from .websocket_client import (
    initialize_websocket_client,
    get_websocket_client,
    shutdown_websocket_client,
    WebSocketClient,
    ConnectionState,
)
from .exceptions import WebSocketConnectionError, WebSocketSubscriptionError

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manager for WebSocket connections and subscriptions.
    
    This class provides system-level APIs for configuring and managing
    WebSocket connections. It reads configuration from environment variables
    or configuration files.
    """
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self._client: Optional[WebSocketClient] = None
        self._config: Dict[str, Any] = {}
    
    def load_config_from_env(self) -> Dict[str, Any]:
        """
        Load WebSocket configuration from environment variables.
        
        Environment variables:
        - WEBSOCKET_ENDPOINT: WebSocket endpoint URL
        - WEBSOCKET_CSRF_TOKEN: CSRF token for authentication
        - WEBSOCKET_MARKET_TYPE: Market type (e.g., 'binance-testnet')
        - WEBSOCKET_SYMBOLS: Comma-separated list of symbols (e.g., 'BTCUSDT,ETHUSDT')
        - WEBSOCKET_RESOLUTIONS: Comma-separated list of resolutions (e.g., '1m,5m,1h')
        
        Returns:
            Configuration dictionary
        """
        config = {
            "endpoint": os.getenv(
                "WEBSOCKET_ENDPOINT",
                "wss://ws.wealthai.cc:18000/market_data"
            ),
            "csrf_token": os.getenv(
                "WEBSOCKET_CSRF_TOKEN",
                "154c3ceaee6ee63a9fb6aa669873d08aec4655944bce20b6e6c413dc4db0ccd5"
            ),
            "market_type": os.getenv("WEBSOCKET_MARKET_TYPE", "binance-testnet"),
        }
        
        # Parse symbols
        symbols_str = os.getenv("WEBSOCKET_SYMBOLS", "")
        if symbols_str:
            config["symbols"] = [s.strip() for s in symbols_str.split(",") if s.strip()]
        else:
            config["symbols"] = []
        
        # Parse resolutions
        resolutions_str = os.getenv("WEBSOCKET_RESOLUTIONS", "")
        if resolutions_str:
            config["resolutions"] = [r.strip() for r in resolutions_str.split(",") if r.strip()]
        else:
            config["resolutions"] = []
        
        return config
    
    def configure(
        self,
        endpoint: Optional[str] = None,
        csrf_token: Optional[str] = None,
        market_type: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        resolutions: Optional[List[str]] = None,
    ) -> None:
        """
        Configure WebSocket connection parameters.
        
        Args:
            endpoint: WebSocket endpoint URL
            csrf_token: CSRF token for authentication
            market_type: Market type (e.g., 'binance-testnet')
            symbols: List of symbols to subscribe to
            resolutions: List of resolutions to subscribe to
        """
        # Load from environment if not provided
        env_config = self.load_config_from_env()
        
        self._config = {
            "endpoint": endpoint or env_config["endpoint"],
            "csrf_token": csrf_token or env_config["csrf_token"],
            "market_type": market_type or env_config["market_type"],
            "symbols": symbols if symbols is not None else env_config["symbols"],
            "resolutions": resolutions if resolutions is not None else env_config["resolutions"],
        }
        
        logger.info(f"WebSocket configured: endpoint={self._config['endpoint']}, "
                   f"symbols={self._config['symbols']}, resolutions={self._config['resolutions']}")
    
    def start(self) -> None:
        """
        Start WebSocket client with current configuration.
        
        Raises:
            WebSocketConnectionError: If connection fails
        """
        if not self._config:
            # Load from environment
            self._config = self.load_config_from_env()
        
        if not self._config.get("symbols") or not self._config.get("resolutions"):
            logger.warning("No symbols or resolutions configured, WebSocket will not start")
            return
        
        try:
            self._client = initialize_websocket_client(
                endpoint=self._config["endpoint"],
                csrf_token=self._config["csrf_token"],
                market_type=self._config["market_type"],
                symbols=self._config["symbols"],
                resolutions=self._config["resolutions"],
            )
            logger.info("WebSocket client started")
        except Exception as e:
            logger.error(f"Failed to start WebSocket client: {e}")
            raise WebSocketConnectionError(f"Failed to start WebSocket: {e}")
    
    def stop(self) -> None:
        """Stop WebSocket client."""
        if self._client:
            self._client.disconnect()
            self._client = None
        shutdown_websocket_client()
        logger.info("WebSocket client stopped")
    
    def update_subscription(self, symbols: List[str], resolutions: List[str]) -> None:
        """
        Update subscription list.
        
        Args:
            symbols: New list of symbols to subscribe to
            resolutions: New list of resolutions to subscribe to
        
        Raises:
            WebSocketSubscriptionError: If update fails
        """
        if not self._client:
            raise WebSocketSubscriptionError("WebSocket client not started")
        
        try:
            self._client.update_subscription(symbols, resolutions)
            self._config["symbols"] = symbols
            self._config["resolutions"] = resolutions
            logger.info(f"Subscription updated: symbols={symbols}, resolutions={resolutions}")
        except Exception as e:
            logger.error(f"Failed to update subscription: {e}")
            raise WebSocketSubscriptionError(f"Failed to update subscription: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get WebSocket connection status.
        
        Returns:
            Dictionary with status information:
            - state: Connection state
            - last_error: Last error message (if any)
            - symbols: Currently subscribed symbols
            - resolutions: Currently subscribed resolutions
        """
        if not self._client:
            return {
                "state": ConnectionState.DISCONNECTED.value,
                "last_error": None,
                "symbols": [],
                "resolutions": [],
            }
        
        return {
            "state": self._client.get_state().value,
            "last_error": self._client.get_last_error(),
            "symbols": self._client.symbols,
            "resolutions": self._client.resolutions,
        }
    
    def is_connected(self) -> bool:
        """
        Check if WebSocket is connected.
        
        Returns:
            True if connected, False otherwise
        """
        if not self._client:
            return False
        return self._client.get_state() == ConnectionState.CONNECTED


# Global manager instance
_global_manager: Optional[WebSocketManager] = None
_manager_lock = threading.Lock()


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.
    
    Returns:
        Global WebSocketManager instance
    """
    global _global_manager
    
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = WebSocketManager()
    
    return _global_manager

