"""
Comprehensive test for all JoinQuant APIs in wealthdata module.

This test verifies that all APIs work correctly when imported via `from wealthdata import *`.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_wealthdata_star_import():
    """Test that all APIs are available via `from wealthdata import *`."""
    # Test star import in a local namespace
    local_globals = {}
    exec("from wealthdata import *", local_globals)
    
    # Verify data access functions
    assert 'get_price' in local_globals, "get_price not available"
    assert 'get_bars' in local_globals, "get_bars not available"
    assert 'get_all_securities' in local_globals, "get_all_securities not available"
    assert 'get_trade_days' in local_globals, "get_trade_days not available"
    assert 'get_index_stocks' in local_globals, "get_index_stocks not available"
    assert 'get_index_weights' in local_globals, "get_index_weights not available"
    assert 'get_fundamentals' in local_globals, "get_fundamentals not available"
    assert 'get_industry' in local_globals, "get_industry not available"
    assert 'get_trades' in local_globals, "get_trades not available"
    
    # Verify strategy functions
    assert 'log' in local_globals, "log not available"
    assert 'g' in local_globals, "g not available"
    assert 'run_daily' in local_globals, "run_daily not available"
    assert 'order_value' in local_globals, "order_value not available"
    assert 'order_target' in local_globals, "order_target not available"
    
    # Verify configuration functions
    assert 'set_benchmark' in local_globals, "set_benchmark not available"
    assert 'set_option' in local_globals, "set_option not available"
    assert 'set_order_cost' in local_globals, "set_order_cost not available"
    assert 'OrderCost' in local_globals, "OrderCost not available"
    
    # Verify all are callable or have expected types
    assert callable(local_globals['get_price']), "get_price not callable"
    assert callable(local_globals['run_daily']), "run_daily not callable"
    assert hasattr(local_globals['log'], 'info'), "log.info not available"
    assert hasattr(local_globals['g'], '__dict__'), "g should be a namespace"
    assert isinstance(local_globals['OrderCost'], type), "OrderCost should be a class"


def test_log_object():
    """Test log object functionality."""
    from wealthdata import log
    
    # Test log object type
    assert hasattr(log, 'info'), "log.info not available"
    assert hasattr(log, 'warn'), "log.warn not available"
    assert hasattr(log, 'error'), "log.error not available"
    assert hasattr(log, 'debug'), "log.debug not available"
    assert hasattr(log, 'set_level'), "log.set_level not available"
    
    # Test log methods are callable
    assert callable(log.info), "log.info not callable"
    assert callable(log.warn), "log.warn not callable"
    assert callable(log.error), "log.error not callable"
    assert callable(log.debug), "log.debug not callable"
    assert callable(log.set_level), "log.set_level not callable"


def test_g_object():
    """Test g object functionality."""
    from wealthdata import g
    
    # Test g object type
    assert hasattr(g, '__dict__'), "g should be a namespace object"
    
    # Test that we can set attributes
    g.test_attr = "test_value"
    assert g.test_attr == "test_value", "g attribute assignment failed"


def test_order_functions():
    """Test order functions are callable."""
    from wealthdata import order_value, order_target
    
    assert callable(order_value), "order_value not callable"
    assert callable(order_target), "order_target not callable"


def test_config_functions():
    """Test configuration functions are callable."""
    from wealthdata import set_benchmark, set_option, set_order_cost, OrderCost
    
    assert callable(set_benchmark), "set_benchmark not callable"
    assert callable(set_option), "set_option not callable"
    assert callable(set_order_cost), "set_order_cost not callable"
    assert isinstance(OrderCost, type), "OrderCost should be a class"


def test_run_daily_function():
    """Test run_daily function is callable."""
    from wealthdata import run_daily
    
    assert callable(run_daily), "run_daily not callable"


def test_order_cost_class():
    """Test OrderCost class can be instantiated."""
    from wealthdata import OrderCost
    
    # Test instantiation with default values
    cost = OrderCost()
    assert cost.close_tax == 0, "OrderCost.close_tax default should be 0"
    assert cost.open_commission == 0, "OrderCost.open_commission default should be 0"
    assert cost.close_commission == 0, "OrderCost.close_commission default should be 0"
    assert cost.min_commission == 0, "OrderCost.min_commission default should be 0"
    
    # Test instantiation with custom values
    cost2 = OrderCost(
        close_tax=0.001,
        open_commission=0.0003,
        close_commission=0.0003,
        min_commission=5
    )
    assert cost2.close_tax == 0.001, "OrderCost.close_tax should be 0.001"
    assert cost2.open_commission == 0.0003, "OrderCost.open_commission should be 0.0003"
    assert cost2.close_commission == 0.0003, "OrderCost.close_commission should be 0.0003"
    assert cost2.min_commission == 5, "OrderCost.min_commission should be 5"


def test_data_access_functions():
    """Test that data access functions are callable."""
    from wealthdata import (
        get_price, get_bars, get_all_securities, get_trade_days,
        get_index_stocks, get_index_weights, get_fundamentals,
        get_industry, get_trades
    )
    
    assert callable(get_price), "get_price not callable"
    assert callable(get_bars), "get_bars not callable"
    assert callable(get_all_securities), "get_all_securities not callable"
    assert callable(get_trade_days), "get_trade_days not callable"
    assert callable(get_index_stocks), "get_index_stocks not callable"
    assert callable(get_index_weights), "get_index_weights not callable"
    assert callable(get_fundamentals), "get_fundamentals not callable"
    assert callable(get_industry), "get_industry not callable"
    assert callable(get_trades), "get_trades not callable"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

