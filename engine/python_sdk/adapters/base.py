"""
Base exchange adapter interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class ExchangeAdapter(ABC):
    """Base class for exchange adapters."""
    
    @abstractmethod
    def get_trading_rule(self, symbol: str) -> dict:
        """
        Query trading rules for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
        
        Returns:
            Trading rule dictionary with:
            - symbol: Symbol code
            - min_quantity: Minimum order quantity
            - quantity_step: Quantity step (quantity must be multiple of this)
            - min_price: Minimum price
            - price_tick: Price tick (price must be multiple of this)
            - price_precision: Price precision (decimal places)
            - quantity_precision: Quantity precision (decimal places)
            - max_leverage: Maximum leverage (default 1.0 if not applicable)
        
        Raises:
            NotFoundError: Symbol not found
            ParseError: Configuration parse error
        """
        pass
    
    @abstractmethod
    def get_commission_rates(self, symbol: str) -> dict:
        """
        Query commission rates for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
        
        Returns:
            Commission rate dictionary with:
            - maker_fee_rate: Maker fee rate (decimal, e.g., 0.0002 for 0.02%)
            - taker_fee_rate: Taker fee rate (decimal, e.g., 0.0004 for 0.04%)
        
        Raises:
            NotFoundError: Symbol not found
            ParseError: Configuration parse error
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate adapter configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of supported trading symbols.
        
        Returns:
            List of symbol identifiers
        """
        pass



