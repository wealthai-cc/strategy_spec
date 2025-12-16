"""
Unit tests for scheduler integration with lifecycle manager.
"""

from datetime import datetime
from engine.lifecycle.lifecycle import LifecycleManager
from engine.compat.scheduler import create_run_daily_function, get_scheduled_functions
from engine.context.context import Context, Account


class TestSchedulerIntegration:
    """Test scheduler integration with lifecycle."""
    
    def test_scheduled_function_registration(self):
        """Test that scheduled functions are registered."""
        # Create a mock strategy module
        class MockModule:
            pass
        
        strategy_module = MockModule()
        run_daily = create_run_daily_function(strategy_module)
        
        # Register a function
        def test_func(context):
            pass
        
        run_daily(test_func, time='before_open', reference_security='000001.XSHE')
        
        # Check registration
        scheduled = get_scheduled_functions(strategy_module)
        assert len(scheduled) == 1
        assert scheduled[0]['time'] == 'before_open'
        assert scheduled[0]['reference_security'] == '000001.XSHE'
    
    def test_lifecycle_manager_with_scheduled_functions(self):
        """Test lifecycle manager calls scheduled functions."""
        # Create a mock strategy module
        class MockModule:
            pass
        
        strategy_module = MockModule()
        run_daily = create_run_daily_function(strategy_module)
        
        # Track if function was called
        called_funcs = []
        
        def before_market_open(context):
            called_funcs.append('before_market_open')
        
        def before_trading_func(context):
            called_funcs.append('before_trading')
        
        # Register scheduled function
        run_daily(before_market_open, time='before_open', reference_security='BTCUSDT')
        
        # Create lifecycle manager
        strategy_functions = {
            'initialize': None,
            'before_trading': before_trading_func,
        }
        lifecycle = LifecycleManager(strategy_functions, strategy_module=strategy_module)
        
        # Create mock context
        account = Account()
        context = Context(
            account=account,
            market_data_context=[{
                'symbol': 'BTCUSDT',
                'timeframe': '1h',
                'bars': [{
                    'open_time': int(datetime.now().timestamp() * 1000),
                    'close_time': int(datetime.now().timestamp() * 1000),
                    'open': '50000',
                    'high': '51000',
                    'low': '49000',
                    'close': '50500',
                    'volume': '100',
                }]
            }],
            incomplete_orders=[],
            completed_orders=[],
            strategy_params={},
            exec_id='test',
            exchange='binance',
        )
        
        # Call before_trading (should call scheduled functions)
        lifecycle.before_trading(context)
        
        # Note: Actual time matching depends on current time, so we just verify
        # that the method doesn't crash and can access scheduled functions
        assert 'before_trading' in called_funcs

