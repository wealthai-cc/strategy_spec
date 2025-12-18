"""
Binance exchange adapter.
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from .base import ExchangeAdapter
from ..exceptions import NotFoundError, ParseError


class BinanceAdapter(ExchangeAdapter):
    """Binance exchange adapter."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Binance adapter.
        
        Args:
            config_path: Optional path to configuration directory
        """
        if config_path is None:
            # Default config path: project_root/config/exchanges/binance/
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "config" / "exchanges" / "binance"
        
        self.config_path = Path(config_path)
        self.trading_rules: Dict[str, dict] = {}
        self.commission_rates: Dict[str, dict] = {}
        
        self._load_config()
        
        if not self.validate_configuration():
            raise ValueError("Invalid Binance adapter configuration")
    
    def _load_config(self) -> None:
        """Load configuration files."""
        trading_rules_file = self.config_path / "trading_rules.yaml"
        commission_rates_file = self.config_path / "commission_rates.yaml"
        
        # Load trading rules
        if trading_rules_file.exists():
            try:
                with open(trading_rules_file, 'r', encoding='utf-8') as f:
                    self.trading_rules = yaml.safe_load(f) or {}
            except Exception as e:
                raise ParseError(f"Failed to parse trading rules: {e}")
        else:
            # Use default empty dict if file doesn't exist
            self.trading_rules = {}
        
        # Load commission rates
        if commission_rates_file.exists():
            try:
                with open(commission_rates_file, 'r', encoding='utf-8') as f:
                    self.commission_rates = yaml.safe_load(f) or {}
            except Exception as e:
                raise ParseError(f"Failed to parse commission rates: {e}")
        else:
            # Use default empty dict if file doesn't exist
            self.commission_rates = {}
    
    def get_trading_rule(self, symbol: str) -> dict:
        """Query trading rules for a symbol."""
        if symbol not in self.trading_rules:
            raise NotFoundError(f"Trading rule not found for {symbol} on Binance")
        
        rule = self.trading_rules[symbol].copy()
        rule['symbol'] = symbol  # Ensure symbol is set
        
        # Validate required fields
        required_fields = [
            'min_quantity', 'quantity_step', 'min_price', 'price_tick',
            'price_precision', 'quantity_precision'
        ]
        for field in required_fields:
            if field not in rule:
                raise ParseError(f"Missing required field '{field}' in trading rule for {symbol}")
        
        # Set default max_leverage if not present
        if 'max_leverage' not in rule:
            rule['max_leverage'] = 1.0
        
        return rule
    
    def get_commission_rates(self, symbol: str) -> dict:
        """Query commission rates for a symbol."""
        if symbol not in self.commission_rates:
            raise NotFoundError(f"Commission rate not found for {symbol} on Binance")
        
        rates = self.commission_rates[symbol].copy()
        
        # Validate required fields
        required_fields = ['maker_fee_rate', 'taker_fee_rate']
        for field in required_fields:
            if field not in rates:
                raise ParseError(f"Missing required field '{field}' in commission rate for {symbol}")
        
        return rates
    
    def validate_configuration(self) -> bool:
        """Validate adapter configuration."""
        # Check if config directory exists
        if not self.config_path.exists():
            return False
        
        # Configuration is valid if we can load it (even if empty)
        # Actual validation happens when querying specific symbols
        return True
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported trading symbols."""
        # Return union of symbols in trading rules and commission rates
        symbols = set(self.trading_rules.keys())
        symbols.update(self.commission_rates.keys())
        return sorted(list(symbols))



