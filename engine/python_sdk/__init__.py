"""
Python SDK for WealthAI strategy execution.

This package provides SDK interfaces for strategy development, including:
- Data adapters for market data access
- Exchange adapters for trading rules and commission rates
- WebSocket market data client (optional)
"""

from .exceptions import NotFoundError, ParseError
from .adapter_registry import get_trading_rule, get_commission_rates

# WebSocket functionality (optional, requires websocket-client)
try:
    from .websocket_manager import get_websocket_manager
    from .websocket_cache import get_websocket_cache
    from .exceptions import WebSocketConnectionError, WebSocketSubscriptionError
    __all__ = [
        'NotFoundError',
        'ParseError',
        'WebSocketConnectionError',
        'WebSocketSubscriptionError',
        'get_trading_rule',
        'get_commission_rates',
        'get_websocket_manager',
        'get_websocket_cache',
    ]
except ImportError:
    # WebSocket functionality not available (websocket-client not installed)
    __all__ = [
        'NotFoundError',
        'ParseError',
        'get_trading_rule',
        'get_commission_rates',
    ]
