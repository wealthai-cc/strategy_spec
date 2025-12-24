"""
Exceptions for Python SDK.
"""


class NotFoundError(Exception):
    """Raised when a resource is not found."""
    pass


class ParseError(Exception):
    """Raised when parsing fails."""
    pass


class WebSocketConnectionError(Exception):
    """Raised when WebSocket connection fails."""
    pass


class WebSocketSubscriptionError(Exception):
    """Raised when WebSocket subscription fails."""
    pass
