"""
Adapter registry for exchange adapters.
"""

import threading
from typing import Dict, Optional
from .adapters.base import ExchangeAdapter
from .adapters.binance_adapter import BinanceAdapter
from .exceptions import NotFoundError

# Adapter registry
_ADAPTER_REGISTRY: Dict[str, type] = {
    "binance": BinanceAdapter,
}

# Adapter instances cache (thread-safe)
_adapter_instances: Dict[str, ExchangeAdapter] = {}
_adapter_lock = threading.Lock()


def register_adapter(exchange: str, adapter_class: type) -> None:
    """
    Register an exchange adapter.
    
    Args:
        exchange: Exchange identifier (e.g., "binance", "okx")
        adapter_class: Adapter class implementing ExchangeAdapter
    """
    if not issubclass(adapter_class, ExchangeAdapter):
        raise TypeError(f"Adapter class must implement ExchangeAdapter")
    
    _ADAPTER_REGISTRY[exchange.lower()] = adapter_class


def get_adapter(exchange: str, config_path: Optional[str] = None) -> ExchangeAdapter:
    """
    Get exchange adapter instance (cached, thread-safe).
    
    Args:
        exchange: Exchange identifier (e.g., "binance", "okx")
        config_path: Optional path to configuration directory
    
    Returns:
        Adapter instance
    
    Raises:
        NotFoundError: Exchange is not supported
    """
    exchange_lower = exchange.lower()
    
    # Check if adapter is registered
    adapter_class = _ADAPTER_REGISTRY.get(exchange_lower)
    if adapter_class is None:
        raise NotFoundError(f"Exchange '{exchange}' is not supported. Supported exchanges: {', '.join(_ADAPTER_REGISTRY.keys())}")
    
    # Get or create adapter instance (thread-safe)
    cache_key = f"{exchange_lower}:{config_path or 'default'}"
    
    if cache_key not in _adapter_instances:
        with _adapter_lock:
            # Double-check after acquiring lock
            if cache_key not in _adapter_instances:
                _adapter_instances[cache_key] = adapter_class(config_path=config_path)
    
    return _adapter_instances[cache_key]


def get_trading_rule(broker: str, symbol: str, config_path: Optional[str] = None) -> dict:
    """
    Query trading rules for a broker and symbol.
    
    Args:
        broker: Exchange identifier (e.g., "binance", "okx")
        symbol: Trading symbol (e.g., "BTCUSDT")
        config_path: Optional path to configuration directory
    
    Returns:
        Trading rule dictionary
    
    Raises:
        NotFoundError: Broker or symbol not found
        ParseError: Configuration parse error
    """
    adapter = get_adapter(broker, config_path=config_path)
    return adapter.get_trading_rule(symbol)


def get_commission_rates(broker: str, symbol: str, config_path: Optional[str] = None) -> dict:
    """
    Query commission rates for a broker and symbol.
    
    Args:
        broker: Exchange identifier (e.g., "binance", "okx")
        symbol: Trading symbol (e.g., "BTCUSDT")
        config_path: Optional path to configuration directory
    
    Returns:
        Commission rate dictionary
    
    Raises:
        NotFoundError: Broker or symbol not found
        ParseError: Configuration parse error
    """
    adapter = get_adapter(broker, config_path=config_path)
    return adapter.get_commission_rates(symbol)



