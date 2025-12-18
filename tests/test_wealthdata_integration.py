"""
Integration tests for wealthdata compatibility layer with strategy execution.
"""

import pytest
import tempfile
import os
from engine.engine import StrategyExecutionEngine


def test_strategy_with_wealthdata():
    """Test strategy using wealthdata module."""
    # Create a strategy file using wealthdata
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import wealthdata

def initialize(context):
    context.symbol = 'BTCUSDT'
    context.ma_period = 20

def handle_bar(context, bar):
    # Use wealthdata.get_price() - JoinQuant style
    df = wealthdata.get_price(context.symbol, count=context.ma_period, frequency='1h')
    
    if len(df) >= context.ma_period:
        ma = df['close'].mean()
        current_price = float(bar.close)
        
        if current_price > ma:
            context.order_buy(context.symbol, 0.1, price=current_price)
""")
        strategy_path = f.name
    
    try:
        engine = StrategyExecutionEngine(strategy_path)
        
        # Generate test data (25 bars for MA calculation)
        bars = []
        base_time = 1000000000
        for i in range(25):
            price = 50000.0 + i * 100
            bars.append({
                "open_time": base_time + i * 3600000,
                "close_time": base_time + (i + 1) * 3600000,
                "open": str(price),
                "high": str(price + 200),
                "low": str(price - 200),
                "close": str(price + 50),
                "volume": str(1000.0 + i * 10),
            })
        
        exec_request = {
            "trigger_type": 1,  # MARKET_DATA_TRIGGER_TYPE
            "trigger_detail": {},
            "market_data_context": [{
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "bars": bars,
            }],
            "account": {
                "account_id": "test_account",
                "account_type": 1,
                "balances": [],
                "positions": [],
                "total_net_value": {"currency_type": 1, "amount": 10000.0},
                "available_margin": {"currency_type": 1, "amount": 10000.0},
                "margin_ratio": 0.0,
                "risk_level": 0.0,
                "leverage": 1.0,
            },
            "incomplete_orders": [],
            "completed_orders": [],
            "exchange": "binance",
            "exec_id": "test_exec",
            "strategy_param": {},
        }
        
        response = engine.execute(exec_request)
        
        # Verify execution succeeded
        assert response["status"] == 0, f"Execution failed: {response.get('error_message')}"
        
        # Verify order was created
        order_ops = response.get("order_op_event", [])
        assert len(order_ops) > 0, "No order operations generated"
        assert order_ops[0]["order_op_type"] == 1  # CREATE_ORDER_OP_TYPE
        
    finally:
        os.unlink(strategy_path)


def test_wealthdata_context_cleanup():
    """Test that context is properly cleaned up after execution."""
    from engine.wealthdata import get_context, clear_context
    
    # Ensure context is cleared
    clear_context()
    
    # Create a simple strategy
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def initialize(context):
    pass

def handle_bar(context, bar):
    pass
""")
        strategy_path = f.name
    
    try:
        engine = StrategyExecutionEngine(strategy_path)
        
        exec_request = {
            "trigger_type": 1,
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
                "account_id": "test",
                "account_type": 1,
                "balances": [],
                "positions": [],
                "total_net_value": {"currency_type": 1, "amount": 10000.0},
                "available_margin": {"currency_type": 1, "amount": 10000.0},
                "margin_ratio": 0.0,
                "risk_level": 0.0,
                "leverage": 1.0,
            },
            "incomplete_orders": [],
            "completed_orders": [],
            "exchange": "binance",
            "exec_id": "test",
            "strategy_param": {},
        }
        
        # Execute strategy
        engine.execute(exec_request)
        
        # Verify context is cleared after execution
        with pytest.raises(RuntimeError, match="Context not available"):
            get_context()
    
    finally:
        os.unlink(strategy_path)



