"""
Market type detection utilities.

Provides functions to detect and identify market types (stock market vs cryptocurrency market)
based on symbol format or explicit configuration.
"""

from enum import Enum
from typing import Optional, Any


class MarketType(Enum):
    """Market type enumeration."""
    A_STOCK = "A_STOCK"      # A股市场
    US_STOCK = "US_STOCK"    # 美股市场
    HK_STOCK = "HK_STOCK"    # 港股市场
    CRYPTO = "CRYPTO"        # 加密货币市场
    UNKNOWN = "UNKNOWN"      # 未知市场类型


def is_stock_market(symbol: str) -> bool:
    """
    Check if a symbol represents a stock market security.
    
    Args:
        symbol: Trading symbol (e.g., '000001.XSHE', 'AAPL.US', '00700.HK', 'BTCUSDT')
    
    Returns:
        True if the symbol represents a stock market security, False otherwise
    """
    if not symbol:
        return False
    
    # JoinQuant format: code.exchange_suffix
    # Examples: 000001.XSHE (A股), AAPL.US (美股), 00700.HK (港股)
    if '.' in symbol:
        suffix = symbol.split('.')[-1]
        # Check if it's a stock market suffix
        if suffix in ['XSHE', 'XSHG', 'US', 'HK']:
            return True
        # If suffix is USDT, it might be a malformed crypto symbol (e.g., BTC.USDT)
        # In this case, we treat it as crypto, not stock
        if suffix == 'USDT':
            return False
    
    # Trading pair format (e.g., BTCUSDT) is cryptocurrency
    return False


def is_crypto_market(symbol: str) -> bool:
    """
    Check if a symbol represents a cryptocurrency trading pair.
    
    Args:
        symbol: Trading symbol
    
    Returns:
        True if the symbol represents a cryptocurrency, False otherwise
    """
    return not is_stock_market(symbol)


def detect_market_type(symbol: str, context: Optional[Any] = None) -> MarketType:
    """
    Detect market type from symbol format or explicit configuration.
    
    Priority:
    1. Explicit configuration (context.market_type or context.params)
    2. Symbol format detection
    3. Default fallback (CRYPTO)
    
    Args:
        symbol: Trading symbol
        context: Optional context object that may contain market_type configuration
    
    Returns:
        MarketType enum value
    """
    # 1. Check explicit configuration (highest priority)
    if context is not None:
        # Check context.market_type attribute
        if hasattr(context, 'market_type') and context.market_type:
            market_type_str = str(context.market_type).upper()
            try:
                return MarketType(market_type_str)
            except ValueError:
                pass
        
        # Check context.params for market_type
        if hasattr(context, 'params') and isinstance(context.params, dict):
            market_type_str = context.params.get('market_type', '').upper()
            if market_type_str:
                try:
                    return MarketType(market_type_str)
                except ValueError:
                    pass
    
    # 2. Detect from symbol format
    if not symbol:
        return MarketType.UNKNOWN
    
    if '.' in symbol:
        suffix = symbol.split('.')[-1]
        if suffix in ['XSHE', 'XSHG']:
            return MarketType.A_STOCK
        elif suffix == 'US':
            return MarketType.US_STOCK
        elif suffix == 'HK':
            return MarketType.HK_STOCK
        elif suffix == 'USDT':
            # Malformed crypto symbol (e.g., BTC.USDT)
            # Log warning but treat as crypto
            return MarketType.CRYPTO
    
    # 3. Default fallback: treat as cryptocurrency
    # Trading pair format (e.g., BTCUSDT) is cryptocurrency
    if not is_stock_market(symbol):
        return MarketType.CRYPTO
    
    return MarketType.UNKNOWN



