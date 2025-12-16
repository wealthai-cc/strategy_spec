"""
JoinQuant compatibility layer.

This module provides compatibility APIs and utilities to support
migration from JoinQuant platform.
"""

from .market_type import (
    is_stock_market,
    is_crypto_market,
    detect_market_type,
    MarketType,
)

__all__ = [
    'is_stock_market',
    'is_crypto_market',
    'detect_market_type',
    'MarketType',
]

