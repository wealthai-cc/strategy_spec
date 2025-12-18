"""
Tests for StrategyExecutionEngine.
"""

import pytest
import tempfile
import os
from engine.engine import StrategyExecutionEngine


def test_engine_execute_market_data_trigger():
    """Test engine execution with market data trigger."""
    # Create a simple strategy
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def initialize(context):
    context.order_placed = False

def handle_bar(context, bar):
    if not context.order_placed:
        context.order_buy("BTCUSDT", 0.1, price=50000.0)
        context.order_placed = True
""")
        strategy_path = f.name
    
    try:
        engine = StrategyExecutionEngine(strategy_path)
        
        exec_request = {
            "trigger_type": 1,  # MARKET_DATA_TRIGGER_TYPE
            "trigger_detail": {},
            "market_data_context": [{
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "bars": [{
                    "open_time": 1000,
                    "close_time": 2000,
                    "open": "100.0",
                    "high": "110.0",
                    "low": "90.0",
                    "close": "105.0",
                    "volume": "1000.0",
                }]
            }],
            "account": {
                "account_id": "test_account",
                "account_type": 1,
                "balances": [],
                "positions": [],
            },
            "incomplete_orders": [],
            "completed_orders": [],
            "exchange": "binance",
            "exec_id": "test_exec",
            "strategy_param": {},
        }
        
        response = engine.execute(exec_request)
        
        assert response["status"] == 0  # SUCCESS
        assert len(response["order_op_event"]) == 1
        assert response["order_op_event"][0]["order_op_type"] == 1  # CREATE_ORDER_OP_TYPE
    
    finally:
        os.unlink(strategy_path)


def test_engine_execute_with_error():
    """Test engine execution with strategy error."""
    # Create a strategy that raises an error
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def initialize(context):
    raise ValueError("Test error")
""")
        strategy_path = f.name
    
    try:
        engine = StrategyExecutionEngine(strategy_path)
        
        exec_request = {
            "trigger_type": 1,
            "trigger_detail": {},
            "market_data_context": [],
            "account": {"account_id": "test"},
            "incomplete_orders": [],
            "completed_orders": [],
            "exchange": "binance",
            "exec_id": "test_exec",
            "strategy_param": {},
        }
        
        response = engine.execute(exec_request)
        
        assert response["status"] == 2  # FAILED
        assert "error_message" in response
        assert len(response["order_op_event"]) == 0
    
    finally:
        os.unlink(strategy_path)



