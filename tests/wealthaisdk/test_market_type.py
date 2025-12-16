"""
Unit tests for market type detection.
"""

import unittest
from engine.compat.market_type import (
    is_stock_market,
    is_crypto_market,
    detect_market_type,
    MarketType,
)


class TestMarketTypeDetection(unittest.TestCase):
    """Test market type detection functions."""
    
    def test_is_stock_market_a_stock(self):
        """Test A-share stock market detection."""
        assert is_stock_market('000001.XSHE') is True
        assert is_stock_market('600000.XSHG') is True
    
    def test_is_stock_market_us_stock(self):
        """Test US stock market detection."""
        assert is_stock_market('AAPL.US') is True
        assert is_stock_market('TSLA.US') is True
    
    def test_is_stock_market_hk_stock(self):
        """Test HK stock market detection."""
        assert is_stock_market('00700.HK') is True
        assert is_stock_market('09988.HK') is True
    
    def test_is_crypto_market(self):
        """Test cryptocurrency market detection."""
        assert is_crypto_market('BTCUSDT') is True
        assert is_crypto_market('ETHUSDT') is True
        assert is_crypto_market('BNBUSDT') is True
    
    def test_is_stock_market_false_for_crypto(self):
        """Test stock market detection returns False for crypto."""
        assert is_stock_market('BTCUSDT') is False
        assert is_stock_market('ETHUSDT') is False
    
    def test_is_crypto_market_false_for_stock(self):
        """Test crypto market detection returns False for stock."""
        assert is_crypto_market('000001.XSHE') is False
        assert is_crypto_market('AAPL.US') is False
    
    def test_malformed_crypto_symbol(self):
        """Test malformed crypto symbol (e.g., BTC.USDT)."""
        # Malformed crypto symbols should be treated as crypto, not stock
        assert is_stock_market('BTC.USDT') is False
        assert is_crypto_market('BTC.USDT') is True
    
    def test_detect_market_type_a_stock(self):
        """Test market type detection for A-share."""
        assert detect_market_type('000001.XSHE') == MarketType.A_STOCK
        assert detect_market_type('600000.XSHG') == MarketType.A_STOCK
    
    def test_detect_market_type_us_stock(self):
        """Test market type detection for US stock."""
        assert detect_market_type('AAPL.US') == MarketType.US_STOCK
    
    def test_detect_market_type_hk_stock(self):
        """Test market type detection for HK stock."""
        assert detect_market_type('00700.HK') == MarketType.HK_STOCK
    
    def test_detect_market_type_crypto(self):
        """Test market type detection for cryptocurrency."""
        assert detect_market_type('BTCUSDT') == MarketType.CRYPTO
        assert detect_market_type('ETHUSDT') == MarketType.CRYPTO
    
    def test_detect_market_type_with_explicit_config(self):
        """Test market type detection with explicit configuration."""
        # Mock context with market_type attribute
        class MockContext:
            def __init__(self, market_type=None):
                self.market_type = market_type
        
        # Explicit configuration should override symbol format
        context = MockContext(market_type='A_STOCK')
        assert detect_market_type('BTCUSDT', context) == MarketType.A_STOCK
        
        context = MockContext(market_type='CRYPTO')
        assert detect_market_type('000001.XSHE', context) == MarketType.CRYPTO
    
    def test_detect_market_type_with_params(self):
        """Test market type detection with context.params."""
        class MockContext:
            def __init__(self, params=None):
                self.params = params or {}
        
        context = MockContext(params={'market_type': 'US_STOCK'})
        assert detect_market_type('BTCUSDT', context) == MarketType.US_STOCK
    
    def test_detect_market_type_empty_symbol(self):
        """Test market type detection with empty symbol."""
        assert detect_market_type('') == MarketType.UNKNOWN
        assert detect_market_type(None) == MarketType.UNKNOWN
    
    def test_detect_market_type_malformed_crypto(self):
        """Test market type detection for malformed crypto symbol."""
        # BTC.USDT should be detected as crypto (not stock)
        assert detect_market_type('BTC.USDT') == MarketType.CRYPTO


if __name__ == '__main__':
    unittest.main()

