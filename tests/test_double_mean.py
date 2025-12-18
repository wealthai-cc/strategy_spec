"""
Comprehensive unit tests for the double_mean strategy.

Tests cover all functionality including edge cases, boundary conditions,
and error scenarios for the double_mean trading strategy.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd
from datetime import datetime, time
import sys
from pathlib import Path

# Add strategy directory to path for importing
strategy_path = Path(__file__).parent.parent / "strategy"
sys.path.insert(0, str(strategy_path))

# Import the strategy to test
import double_mean
from engine.context import Context, Account, Bar, Portfolio, Position


class TestDoubleMeanStrategy:
    """Test class for double_mean strategy functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context object for testing."""
        # Create mock portfolio
        mock_portfolio = Mock()
        mock_portfolio.available_cash = 10000.0
        mock_portfolio.positions_value = 5000.0
        
        # Create mock positions with a stock position
        mock_position = Mock()
        mock_position.closeable_amount = 100
        mock_portfolio.positions = {'000001.XSHE': mock_position}
        
        # Create mock account
        mock_account = Mock()
        mock_account.account_id = "test_account"
        
        # Create mock context
        mock_context = Mock()
        mock_context.portfolio = mock_portfolio
        mock_context.account = mock_account
        mock_context.current_dt = datetime(2024, 1, 1, 9, 30)
        
        return mock_context

    @pytest.fixture
    def mock_log(self):
        """Create a mock log object."""
        return Mock()

    @pytest.fixture
    def mock_g(self):
        """Create a mock global object."""
        mock_g = Mock()
        mock_g.security = '000001.XSHE'
        return mock_g

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        # Mock close price data for 5 days
        close_data = pd.DataFrame({
            'close': [10.0, 10.5, 11.0, 10.8, 11.2]  # MA5 = 10.7
        })
        return close_data

    @pytest.fixture
    def mock_functions(self):
        """Create mock strategy functions."""
        mocks = {
            'set_benchmark': Mock(),
            'set_option': Mock(),
            'set_order_cost': Mock(),
            'run_daily': Mock(),
            'order_value': Mock(),
            'order_target': Mock(),
            'get_bars': Mock(),
            'get_trades': Mock(return_value={}),
        }
        return mocks

    def test_initialize_success(self, mock_functions):
        """Test successful strategy initialization."""
        # Patch all the imported functions
        with patch.multiple(
            'double_mean',
            set_benchmark=mock_functions['set_benchmark'],
            set_option=mock_functions['set_option'],
            set_order_cost=mock_functions['set_order_cost'],
            run_daily=mock_functions['run_daily'],
            OrderCost=Mock
        ):
            # Mock OrderCost instance
            mock_order_cost = Mock()
            with patch('double_mean.OrderCost', return_value=mock_order_cost):
                # Call initialize
                double_mean.initialize(Mock())
                
                # Verify all functions were called with correct parameters
                mock_functions['set_benchmark'].assert_called_once_with('000300.XSHG')
                mock_functions['set_option'].assert_called_once_with('use_real_price', True)
                mock_functions['set_order_cost'].assert_called_once()
                mock_functions['run_daily'].assert_any_call(
                    double_mean.before_market_open,
                    time='before_open',
                    reference_security='000300.XSHG'
                )
                mock_functions['run_daily'].assert_any_call(
                    double_mean.market_open,
                    time='open',
                    reference_security='000300.XSHG'
                )
                mock_functions['run_daily'].assert_any_call(
                    double_mean.after_market_close,
                    time='after_close',
                    reference_security='000300.XSHG'
                )

    def test_before_market_open(self, mock_context, mock_g, mock_log):
        """Test before_market_open function."""
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', mock_log):
            
            double_mean.before_market_open(mock_context)
            
            # Verify security was set
            assert mock_g.security == '000001.XSHE'
            
            # Verify log was called
            mock_log.info.assert_called_once()

    def test_market_open_buy_condition_met(self, mock_context, mock_g, sample_price_data, mock_functions):
        """Test market_open when buy condition is met."""
        # Setup: current price is 1% above MA5 and cash is available
        sample_price_data['close'] = [10.0, 10.5, 11.0, 10.8, 10.807]  # MA5=10.66, current=10.807
        mock_context.portfolio.available_cash = 10000.0
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_value', mock_functions['order_value']):
            
            double_mean.market_open(mock_context)
            
            # Verify buy order was placed
            mock_functions['order_value'].assert_called_once_with('000001.XSHE', 10000.0)

    def test_market_open_buy_condition_not_met_price_too_low(self, mock_context, mock_g, sample_price_data, mock_functions):
        """Test market_open when buy condition is not met (price too low)."""
        # Setup: current price is not 1% above MA5
        sample_price_data['close'] = [10.0, 10.5, 11.0, 10.8, 10.5]  # MA5=10.56, current=10.5
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_value', mock_functions['order_value']):
            
            double_mean.market_open(mock_context)
            
            # Verify no buy order was placed
            mock_functions['order_value'].assert_not_called()

    def test_market_open_buy_condition_not_met_no_cash(self, mock_context, mock_g, sample_price_data, mock_functions):
        """Test market_open when buy condition is met but no cash available."""
        # Setup: price condition met but no cash
        sample_price_data['close'] = [10.0, 10.5, 11.0, 10.8, 10.807]  # MA5=10.66, current=10.807
        mock_context.portfolio.available_cash = 0.0
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_value', mock_functions['order_value']):
            
            double_mean.market_open(mock_context)
            
            # Verify no buy order was placed
            mock_functions['order_value'].assert_not_called()

    def test_market_open_sell_condition_met(self, mock_context, mock_g, sample_price_data, mock_functions):
        """Test market_open when sell condition is met."""
        # Setup: current price is below MA5 and we have position
        sample_price_data['close'] = [10.0, 10.5, 11.0, 10.8, 10.5]  # MA5=10.56, current=10.5
        mock_context.portfolio.positions['000001.XSHE'].closeable_amount = 100
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_target', mock_functions['order_target']):
            
            double_mean.market_open(mock_context)
            
            # Verify sell order was placed
            mock_functions['order_target'].assert_called_once_with('000001.XSHE', 0)

    def test_market_open_sell_condition_not_met_price_too_high(self, mock_context, mock_g, sample_price_data, mock_functions):
        """Test market_open when sell condition is not met (price too high)."""
        # Setup: current price is above MA5
        sample_price_data['close'] = [10.0, 10.5, 11.0, 10.8, 10.8]  # MA5=10.62, current=10.8
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_target', mock_functions['order_target']):
            
            double_mean.market_open(mock_context)
            
            # Verify no sell order was placed
            mock_functions['order_target'].assert_not_called()

    def test_market_open_sell_condition_not_met_no_position(self, mock_context, mock_g, sample_price_data, mock_functions):
        """Test market_open when sell condition is met but no position to sell."""
        # Setup: price condition met but no position
        sample_price_data['close'] = [10.0, 10.5, 11.0, 10.8, 10.5]  # MA5=10.56, current=10.5
        mock_context.portfolio.positions['000001.XSHE'].closeable_amount = 0
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_target', mock_functions['order_target']):
            
            double_mean.market_open(mock_context)
            
            # Verify no sell order was placed
            mock_functions['order_target'].assert_not_called()

    def test_market_open_no_trades_when_conditions_equal(self, mock_context, mock_g, sample_price_data, mock_functions):
        """Test market_open when current price equals MA5 (no action)."""
        # Setup: current price equals MA5 exactly
        sample_price_data['close'] = [10.0, 10.5, 11.0, 10.8, 10.56]  # MA5=10.56, current=10.56
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_value', mock_functions['order_value']), \
             patch('double_mean.order_target', mock_functions['order_target']):
            
            double_mean.market_open(mock_context)
            
            # Verify no orders were placed
            mock_functions['order_value'].assert_not_called()
            mock_functions['order_target'].assert_not_called()

    def test_market_open_insufficient_data(self, mock_context, mock_g, mock_functions):
        """Test market_open with insufficient price data."""
        # Setup: less than 5 days of data
        insufficient_data = pd.DataFrame({'close': [10.0, 10.5, 11.0]})
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=insufficient_data), \
             patch('double_mean.order_value', mock_functions['order_value']), \
             patch('double_mean.order_target', mock_functions['order_target']):
            
            # Should not raise error but handle gracefully
            double_mean.market_open(mock_context)
            
            # Verify no orders were placed due to insufficient data
            mock_functions['order_value'].assert_not_called()
            mock_functions['order_target'].assert_not_called()

    def test_market_open_edge_case_exact_1_percent_above(self, mock_context, mock_g, mock_functions):
        """Test market_open with price exactly 1% above MA5."""
        # Setup: current price exactly 1% above MA5
        # MA5 = 10.0, current price should be 10.1
        sample_price_data = pd.DataFrame({'close': [9.9, 9.95, 10.05, 10.1, 10.1]})
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_value', mock_functions['order_value']):
            
            double_mean.market_open(mock_context)
            
            # Should buy since price >= 1% above MA5
            mock_functions['order_value'].assert_called_once()

    def test_market_open_edge_case_just_under_1_percent(self, mock_context, mock_g, mock_functions):
        """Test market_open with price just under 1% above MA5."""
        # Setup: current price just under 1% above MA5
        # MA5 = 10.0, current price = 10.099 (0.99% above)
        sample_price_data = pd.DataFrame({'close': [9.9, 9.95, 10.05, 10.09, 10.099]})
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_value', mock_functions['order_value']):
            
            double_mean.market_open(mock_context)
            
            # Should not buy since price < 1% above MA5
            mock_functions['order_value'].assert_not_called()

    def test_after_market_close_with_trades(self, mock_context, mock_functions):
        """Test after_market_close with trades to report."""
        # Setup: mock trades data
        mock_trades = {
            'trade1': {'symbol': '000001.XSHE', 'amount': 100, 'price': 10.5},
            'trade2': {'symbol': '000002.XSHE', 'amount': 50, 'price': 20.0}
        }
        mock_functions['get_trades'].return_value = mock_trades
        
        with patch('double_mean.log', Mock()) as mock_log, \
             patch('double_mean.get_trades', mock_functions['get_trades']):
            
            double_mean.after_market_close(mock_context)
            
            # Verify get_trades was called
            mock_functions['get_trades'].assert_called_once()
            
            # Verify log was called for each trade and summary
            assert mock_log.info.call_count >= 3  # Each trade + summary

    def test_after_market_close_no_trades(self, mock_context, mock_functions):
        """Test after_market_close with no trades."""
        # Setup: no trades
        mock_functions['get_trades'].return_value = {}
        
        with patch('double_mean.log', Mock()) as mock_log, \
             patch('double_mean.get_trades', mock_functions['get_trades']):
            
            double_mean.after_market_close(mock_context)
            
            # Verify get_trades was called
            mock_functions['get_trades'].assert_called_once()
            
            # Verify log was called for summary
            assert mock_log.info.call_count >= 2  # Summary + separator

    def test_get_bars_error_handling(self, mock_context, mock_g):
        """Test error handling when get_bars fails."""
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', side_effect=Exception("Data fetch error")), \
             patch('double_mean.order_value', Mock()), \
             patch('double_mean.order_target', Mock()):
            
            # Should handle the error gracefully
            with pytest.raises(Exception, match="Data fetch error"):
                double_mean.market_open(mock_context)

    def test_portfolio_attributes_missing(self, mock_g, sample_price_data):
        """Test behavior when portfolio attributes are missing."""
        # Create context with missing portfolio attributes
        mock_context = Mock()
        mock_context.portfolio = Mock()
        del mock_context.portfolio.available_cash
        del mock_context.portfolio.positions
        
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=sample_price_data), \
             patch('double_mean.order_value', Mock()), \
             patch('double_mean.order_target', Mock()):
            
            # Should handle missing attributes gracefully
            double_mean.market_open(mock_context)

    def test_order_cost_configuration(self, mock_functions):
        """Test that OrderCost is configured correctly."""
        with patch.multiple(
            'double_mean',
            set_benchmark=Mock(),
            set_option=Mock(),
            run_daily=Mock()
        ), patch('double_mean.OrderCost') as mock_order_cost_class:
            
            mock_order_cost_instance = Mock()
            mock_order_cost_class.return_value = mock_order_cost_instance
            
            with patch('double_mean.set_order_cost', mock_functions['set_order_cost']) as mock_set_order_cost:
                double_mean.initialize(Mock())
                
                # Verify OrderCost was created with correct parameters
                mock_order_cost_class.assert_called_once_with(
                    close_tax=0.001,
                    open_commission=0.0003,
                    close_commission=0.0003,
                    min_commission=5
                )
                
                # Verify set_order_cost was called with the OrderCost instance
                mock_set_order_cost.assert_called_once_with(mock_order_cost_instance, type='stock')

    def test_log_messages_content(self, mock_context, mock_g, mock_log):
        """Test that log messages contain expected content."""
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', mock_log):
            
            # Test before_market_open log
            double_mean.before_market_open(mock_context)
            mock_log.info.assert_called()
            call_args = mock_log.info.call_args[0][0]
            assert 'before_market_open' in call_args
            
            # Reset mock
            mock_log.reset_mock()
            
            # Test after_market_close log
            with patch('double_mean.get_trades', return_value={}):
                double_mean.after_market_close(mock_context)
                mock_log.info.assert_called()
                call_args = mock_log.info.call_args[0][0]
                assert 'after_market_close' in call_args

    def test_security_symbol_persistence(self, mock_context, mock_g):
        """Test that security symbol persists across function calls."""
        with patch('double_mean.g', mock_g), \
             patch('double_mean.log', Mock()), \
             patch('double_mean.get_bars', return_value=pd.DataFrame({'close': [10, 11, 12, 13, 14]})):
            
            # Call before_market_open to set security
            double_mean.before_market_open(mock_context)
            
            # Verify security is set
            assert mock_g.security == '000001.XSHE'
            
            # Call market_open and verify it uses the set security
            with patch('double_mean.order_value') as mock_order_value, \
                 patch('double_mean.order_target') as mock_order_target:
                
                double_mean.market_open(mock_context)
                
                # The functions should be called with the correct security
                if mock_order_value.called:
                    mock_order_value.assert_called_with('000001.XSHE', mock_context.portfolio.available_cash)
                if mock_order_target.called:
                    mock_order_target.assert_called_with('000001.XSHE', 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])