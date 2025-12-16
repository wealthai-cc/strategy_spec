"""
Unit tests for Context and Portfolio extensions.
"""

import pytest
from datetime import datetime
from engine.context.context import Context, Portfolio, Account, Bar


class TestPortfolioExtension:
    """Test Portfolio class extensions."""
    
    def test_portfolio_positions_dict_access(self):
        """Test dictionary-style position access."""
        portfolio = Portfolio()
        
        positions = [
            {'symbol': 'BTCUSDT', 'quantity': 0.5, 'average_cost_price': 50000},
            {'symbol': 'ETHUSDT', 'quantity': 2.0, 'average_cost_price': 3000},
        ]
        portfolio.set_positions(positions)
        
        # Test dictionary access
        assert 'BTCUSDT' in portfolio.positions
        assert portfolio.positions['BTCUSDT']['quantity'] == 0.5
        assert portfolio.positions['ETHUSDT']['quantity'] == 2.0
    
    def test_portfolio_available_cash(self):
        """Test available_cash property."""
        portfolio = Portfolio()
        portfolio.set_available_cash(10000.0)
        
        assert portfolio.available_cash == 10000.0
    
    def test_portfolio_positions_value(self):
        """Test positions_value property."""
        portfolio = Portfolio()
        portfolio.set_positions_value(50000.0)
        
        assert portfolio.positions_value == 50000.0
    
    def test_portfolio_positions_list_access(self):
        """Test list-style position access."""
        portfolio = Portfolio()
        
        positions = [
            {'symbol': 'BTCUSDT', 'quantity': 0.5},
            {'symbol': 'ETHUSDT', 'quantity': 2.0},
        ]
        portfolio.set_positions(positions)
        
        # Test list access
        positions_list = portfolio.get_positions_list()
        assert len(positions_list) == 2
        assert positions_list[0]['symbol'] == 'BTCUSDT'


class TestContextExtension:
    """Test Context class extensions."""
    
    def test_context_current_dt(self):
        """Test current_dt property."""
        account = Account()
        bar = Bar(
            open_time=1609459200000,  # 2021-01-01 00:00:00 UTC
            close_time=1609462800000,  # 2021-01-01 01:00:00 UTC
            open="50000",
            high="51000",
            low="49000",
            close="50500",
            volume="100",
        )
        
        market_data_context = [{
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'bars': [{
                'open_time': 1609459200000,
                'close_time': 1609462800000,
                'open': '50000',
                'high': '51000',
                'low': '49000',
                'close': '50500',
                'volume': '100',
            }]
        }]
        
        context = Context(
            account=account,
            market_data_context=market_data_context,
            incomplete_orders=[],
            completed_orders=[],
            strategy_params={},
            exec_id='test',
            exchange='binance',
        )
        
        assert context.current_dt is not None
        assert isinstance(context.current_dt, datetime)
        # Verify timestamp conversion
        expected_dt = datetime.fromtimestamp(1609462800000 / 1000.0)
        assert context.current_dt == expected_dt
    
    def test_context_current_dt_none(self):
        """Test current_dt when current_bar is None."""
        account = Account()
        context = Context(
            account=account,
            market_data_context=[],
            incomplete_orders=[],
            completed_orders=[],
            strategy_params={},
            exec_id='test',
            exchange='binance',
        )
        
        assert context.current_dt is None
    
    def test_portfolio_available_cash_from_account(self):
        """Test portfolio available_cash calculation from account."""
        account = Account()
        account.available_margin = {'USDT': 10000.0}
        
        context = Context(
            account=account,
            market_data_context=[],
            incomplete_orders=[],
            completed_orders=[],
            strategy_params={},
            exec_id='test',
            exchange='binance',
        )
        
        # Should calculate available cash from account
        assert context.portfolio.available_cash > 0
    
    def test_portfolio_positions_dict_from_account(self):
        """Test portfolio positions dictionary from account."""
        account = Account()
        account.positions = [
            {'symbol': 'BTCUSDT', 'quantity': 0.5},
            {'symbol': 'ETHUSDT', 'quantity': 2.0},
        ]
        
        context = Context(
            account=account,
            market_data_context=[],
            incomplete_orders=[],
            completed_orders=[],
            strategy_params={},
            exec_id='test',
            exchange='binance',
        )
        
        # Test dictionary access
        assert 'BTCUSDT' in context.portfolio.positions
        assert context.portfolio.positions['BTCUSDT']['quantity'] == 0.5
        assert 'ETHUSDT' in context.portfolio.positions
        assert context.portfolio.positions['ETHUSDT']['quantity'] == 2.0

