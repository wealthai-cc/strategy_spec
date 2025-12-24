"""
WebSocket client for WealthAI market data service.

This module provides a WebSocket client that connects to WealthAI's market data
service and receives real-time market data. The client runs as a background
service and stores received data in the global cache.
"""

import json
import logging
import threading
import time
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
import websocket

from .exceptions import WebSocketConnectionError, WebSocketSubscriptionError
from .websocket_cache import get_websocket_cache

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class WebSocketClient:
    """
    WebSocket client for WealthAI market data service.
    
    This client connects to the WealthAI WebSocket service, sends subscription
    messages, and receives real-time market data. Received data is stored in
    the global cache for access by data adapters.
    """
    
    def __init__(
        self,
        endpoint: str = "wss://ws.wealthai.cc:18000/market_data",
        csrf_token: str = "154c3ceaee6ee63a9fb6aa669873d08aec4655944bce20b6e6c413dc4db0ccd5",
        market_type: str = "binance-testnet",
        symbols: Optional[List[str]] = None,
        resolutions: Optional[List[str]] = None,
        max_reconnect_attempts: int = 3,
        reconnect_delay_base: float = 1.0,
    ):
        """
        Initialize WebSocket client.
        
        Args:
            endpoint: WebSocket endpoint URL
            csrf_token: CSRF token for authentication
            market_type: Market type (e.g., 'binance-testnet')
            symbols: List of symbols to subscribe to
            resolutions: List of resolutions to subscribe to (e.g., ['1m', '5m'])
            max_reconnect_attempts: Maximum number of reconnection attempts
            reconnect_delay_base: Base delay for exponential backoff (seconds)
        """
        self.endpoint = endpoint
        self.csrf_token = csrf_token
        self.market_type = market_type
        self.symbols = symbols or []
        self.resolutions = resolutions or []
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay_base = reconnect_delay_base
        
        self._ws: Optional[websocket.WebSocketApp] = None
        self._state = ConnectionState.DISCONNECTED
        self._lock = threading.RLock()
        self._reconnect_attempts = 0
        self._reconnect_thread: Optional[threading.Thread] = None
        self._should_reconnect = False
        self._cache = get_websocket_cache()
        self._last_error: Optional[str] = None
        
        # Callbacks
        self._on_state_change: Optional[Callable[[ConnectionState], None]] = None
    
    def set_state(self, new_state: ConnectionState) -> None:
        """Update connection state and notify listeners."""
        with self._lock:
            old_state = self._state
            self._state = new_state
            
            if old_state != new_state:
                logger.info(f"WebSocket state changed: {old_state.value} -> {new_state.value}")
                
                if self._on_state_change:
                    try:
                        self._on_state_change(new_state)
                    except Exception as e:
                        logger.error(f"Error in state change callback: {e}")
    
    def get_state(self) -> ConnectionState:
        """Get current connection state."""
        with self._lock:
            return self._state
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message."""
        with self._lock:
            return self._last_error
    
    def set_on_state_change(self, callback: Callable[[ConnectionState], None]) -> None:
        """Set callback for state changes."""
        self._on_state_change = callback
    
    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        """Handle WebSocket connection opened."""
        logger.info(f"WebSocket connected to {self.endpoint}")
        self.set_state(ConnectionState.CONNECTED)
        self._reconnect_attempts = 0
        
        # Send CONNECT message
        self._send_connect_message()
    
    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")
            
            if msg_type == "CONNECTED":
                logger.info("WebSocket subscription confirmed")
                self.set_state(ConnectionState.CONNECTED)
            elif msg_type == "BAR" or msg_type == "KLINE":
                # Handle market data
                self._handle_market_data(data)
            elif msg_type == "ERROR":
                error_msg = data.get("message", "Unknown error")
                logger.error(f"WebSocket error: {error_msg}")
                self._last_error = error_msg
                # Don't raise here, just log and set error state
                # Let the caller decide whether to raise based on error type
                self.set_state(ConnectionState.ERROR)
            else:
                logger.debug(f"Received message type: {msg_type}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}, message: {message[:100]}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """Handle WebSocket error."""
        error_msg = str(error)
        logger.error(f"WebSocket error: {error_msg}")
        
        with self._lock:
            self._last_error = error_msg
        
        # Don't change state here, let on_close handle reconnection
        self.set_state(ConnectionState.ERROR)
    
    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        """Handle WebSocket connection closed."""
        logger.warning(f"WebSocket closed: status={close_status_code}, msg={close_msg}")
        self.set_state(ConnectionState.DISCONNECTED)
        
        # Attempt reconnection if enabled
        if self._should_reconnect:
            self._attempt_reconnect()
    
    def _send_connect_message(self) -> None:
        """Send CONNECT message to subscribe to market data."""
        if not self.symbols or not self.resolutions:
            logger.warning("No symbols or resolutions configured, skipping subscription")
            return
        
        connect_msg = {
            "type": "CONNECT",
            "request_id": "1",
            "symbols": self.symbols,
            "resolutions": self.resolutions,
            "csrf_token": self.csrf_token,
            "market_type": self.market_type
        }
        
        try:
            message = json.dumps(connect_msg)
            if self._ws:
                self._ws.send(message)
                logger.info(f"Sent CONNECT message: symbols={self.symbols}, resolutions={self.resolutions}")
        except Exception as e:
            logger.error(f"Failed to send CONNECT message: {e}")
            raise WebSocketSubscriptionError(f"Failed to send subscription: {e}")
    
    def _handle_market_data(self, data: Dict[str, Any]) -> None:
        """Handle incoming market data and store in cache."""
        try:
            symbol = data.get("symbol", "")
            timeframe = data.get("timeframe") or data.get("resolution", "")
            
            if not symbol or not timeframe:
                logger.warning(f"Invalid market data: missing symbol or timeframe, data={data}")
                return
            
            # Extract bar data
            bar = {
                "open_time": data.get("open_time", 0),
                "close_time": data.get("close_time", 0),
                "open": str(data.get("open", "0")),
                "high": str(data.get("high", "0")),
                "low": str(data.get("low", "0")),
                "close": str(data.get("close", "0")),
                "volume": str(data.get("volume", "0")),
            }
            
            # Store in cache
            self._cache.add_bar(symbol, timeframe, bar)
            logger.debug(f"Cached bar: {symbol} {timeframe} at {bar['close_time']}")
            
        except Exception as e:
            logger.error(f"Error handling market data: {e}, data={data}")
    
    def _attempt_reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        if self._reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            self.set_state(ConnectionState.ERROR)
            self._should_reconnect = False
            return
        
        self._reconnect_attempts += 1
        delay = self.reconnect_delay_base * (2 ** (self._reconnect_attempts - 1))
        
        logger.info(f"Attempting reconnection {self._reconnect_attempts}/{self.max_reconnect_attempts} in {delay:.1f}s")
        self.set_state(ConnectionState.RECONNECTING)
        
        def reconnect():
            time.sleep(delay)
            if self._should_reconnect:
                try:
                    self.connect()
                except Exception as e:
                    logger.error(f"Reconnection failed: {e}")
                    if self._should_reconnect:
                        self._attempt_reconnect()
        
        self._reconnect_thread = threading.Thread(target=reconnect, daemon=True)
        self._reconnect_thread.start()
    
    def connect(self) -> None:
        """Connect to WebSocket server."""
        with self._lock:
            if self._state in (ConnectionState.CONNECTING, ConnectionState.CONNECTED):
                logger.warning("WebSocket already connecting or connected")
                return
            
            self.set_state(ConnectionState.CONNECTING)
            self._should_reconnect = True
        
        try:
            self._ws = websocket.WebSocketApp(
                self.endpoint,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Run in a separate thread
            def run_forever():
                if self._ws:
                    self._ws.run_forever()
            
            thread = threading.Thread(target=run_forever, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"Failed to create WebSocket connection: {e}")
            self.set_state(ConnectionState.ERROR)
            self._last_error = str(e)
            raise WebSocketConnectionError(f"Failed to connect: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        with self._lock:
            self._should_reconnect = False
        
        if self._ws:
            try:
                self._ws.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        
        self.set_state(ConnectionState.DISCONNECTED)
    
    def update_subscription(self, symbols: List[str], resolutions: List[str]) -> None:
        """
        Update subscription list.
        
        Args:
            symbols: New list of symbols to subscribe to
            resolutions: New list of resolutions to subscribe to
        """
        with self._lock:
            self.symbols = symbols
            self.resolutions = resolutions
        
        # If connected, send new CONNECT message
        if self._state == ConnectionState.CONNECTED:
            self._send_connect_message()


# Global client instance
_global_client: Optional[WebSocketClient] = None
_client_lock = threading.Lock()


def get_websocket_client() -> Optional[WebSocketClient]:
    """
    Get the global WebSocket client instance.
    
    Returns:
        Global WebSocketClient instance, or None if not initialized
    """
    return _global_client


def initialize_websocket_client(
    endpoint: Optional[str] = None,
    csrf_token: Optional[str] = None,
    market_type: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    resolutions: Optional[List[str]] = None,
) -> WebSocketClient:
    """
    Initialize and start the global WebSocket client.
    
    Args:
        endpoint: WebSocket endpoint URL (uses default if not provided)
        csrf_token: CSRF token (uses default if not provided)
        market_type: Market type (uses default if not provided)
        symbols: List of symbols to subscribe to
        resolutions: List of resolutions to subscribe to
    
    Returns:
        Initialized WebSocketClient instance
    """
    global _global_client
    
    with _client_lock:
        if _global_client is not None:
            logger.warning("WebSocket client already initialized")
            return _global_client
        
        _global_client = WebSocketClient(
            endpoint=endpoint,
            csrf_token=csrf_token,
            market_type=market_type,
            symbols=symbols,
            resolutions=resolutions,
        )
        
        # Auto-connect if symbols and resolutions are provided
        if symbols and resolutions:
            _global_client.connect()
        
        return _global_client


def shutdown_websocket_client() -> None:
    """Shutdown the global WebSocket client."""
    global _global_client
    
    with _client_lock:
        if _global_client is not None:
            _global_client.disconnect()
            _global_client = None

