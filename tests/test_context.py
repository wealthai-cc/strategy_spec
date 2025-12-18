"""
Tests for Context object.
"""

import pytest
from engine.context import Context, Account, Order, Bar


def test_context_initialization():
    """Test Context initialization."""
    account = Account(account_id="test_account")
    context = Context(
        account=account,
        market_data_context=[],
        incomplete_orders=[],
        completed_orders=[],
        strategy_params={},
        exec_id="test_exec",
        exchange="binance",
    )
    
    assert context.account == account
    assert context.exec_id == "test_exec"
    assert context.exchange == "binance"


def test_context_custom_attributes():
    """Test storing custom attributes on context."""
    account = Account(account_id="test_account")
    context = Context(
        account=account,
        market_data_context=[],
        incomplete_orders=[],
        completed_orders=[],
        strategy_params={},
        exec_id="test_exec",
        exchange="binance",
    )
    
    # Store custom attribute
    context.symbol = "BTCUSDT"
    context.ma_period = 20
    
    assert context.symbol == "BTCUSDT"
    assert context.ma_period == 20


def test_context_history():
    """Test history method."""
    account = Account(account_id="test_account")
    market_data = [{
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "bars": [
            {
                "open_time": 1000,
                "close_time": 2000,
                "open": "100.0",
                "high": "110.0",
                "low": "90.0",
                "close": "105.0",
                "volume": "1000.0",
            },
            {
                "open_time": 2000,
                "close_time": 3000,
                "open": "105.0",
                "high": "115.0",
                "low": "95.0",
                "close": "110.0",
                "volume": "1100.0",
            },
        ]
    }]
    
    context = Context(
        account=account,
        market_data_context=market_data,
        incomplete_orders=[],
        completed_orders=[],
        strategy_params={},
        exec_id="test_exec",
        exchange="binance",
    )
    
    bars = context.history("BTCUSDT", 2, "1h")
    assert len(bars) == 2
    assert bars[0].close == "105.0"
    assert bars[1].close == "110.0"


def test_context_order_buy():
    """Test order_buy method."""
    account = Account(account_id="test_account")
    context = Context(
        account=account,
        market_data_context=[],
        incomplete_orders=[],
        completed_orders=[],
        strategy_params={},
        exec_id="test_exec",
        exchange="binance",
    )
    
    order = context.order_buy("BTCUSDT", 0.1, price=50000.0)
    
    assert order.symbol == "BTCUSDT"
    assert order.qty == 0.1
    assert order.limit_price == "50000.0"
    assert order.direction_type == 1  # BUY
    
    # Check order operations
    ops = context.get_order_operations()
    assert len(ops) == 1
    assert ops[0]["order_op_type"] == 1  # CREATE_ORDER_OP_TYPE


def test_context_order_sell():
    """Test order_sell method."""
    account = Account(account_id="test_account")
    context = Context(
        account=account,
        market_data_context=[],
        incomplete_orders=[],
        completed_orders=[],
        strategy_params={},
        exec_id="test_exec",
        exchange="binance",
    )
    
    order = context.order_sell("BTCUSDT", 0.1, price=50000.0)
    
    assert order.symbol == "BTCUSDT"
    assert order.qty == 0.1
    assert order.direction_type == 2  # SELL


def test_context_cancel_order():
    """Test cancel_order method."""
    account = Account(account_id="test_account")
    incomplete_order = Order(
        order_id="order123",
        unique_id="unique123",
        symbol="BTCUSDT",
    )
    
    context = Context(
        account=account,
        market_data_context=[],
        incomplete_orders=[incomplete_order],
        completed_orders=[],
        strategy_params={},
        exec_id="test_exec",
        exchange="binance",
    )
    
    result = context.cancel_order("order123")
    assert result is True
    
    # Check order operations
    ops = context.get_order_operations()
    assert len(ops) == 1
    assert ops[0]["order_op_type"] == 2  # WITHDRAW_ORDER_OP_TYPE



