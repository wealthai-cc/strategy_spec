"""
Tests for StrategyLoader.
"""

import pytest
import tempfile
import os
from engine.loader import StrategyLoader


def test_load_strategy_with_initialize():
    """Test loading strategy with initialize function."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def initialize(context):
    context.symbol = "BTCUSDT"
""")
        strategy_path = f.name
    
    try:
        loader = StrategyLoader(strategy_path)
        functions = loader.load()
        
        assert "initialize" in functions
        assert functions["initialize"] is not None
        assert loader.has_function("initialize")
    finally:
        os.unlink(strategy_path)


def test_load_strategy_missing_initialize():
    """Test loading strategy without required initialize function."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def handle_bar(context, bar):
    pass
""")
        strategy_path = f.name
    
    try:
        loader = StrategyLoader(strategy_path)
        with pytest.raises(ValueError, match="must define 'initialize' function"):
            loader.load()
    finally:
        os.unlink(strategy_path)


def test_load_strategy_with_all_functions():
    """Test loading strategy with all lifecycle functions."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def initialize(context):
    pass

def before_trading(context):
    pass

def handle_bar(context, bar):
    pass

def on_order(context, order):
    pass

def on_risk_event(context, event):
    pass
""")
        strategy_path = f.name
    
    try:
        loader = StrategyLoader(strategy_path)
        functions = loader.load()
        
        assert loader.has_function("initialize")
        assert loader.has_function("before_trading")
        assert loader.has_function("handle_bar")
        assert loader.has_function("on_order")
        assert loader.has_function("on_risk_event")
    finally:
        os.unlink(strategy_path)



