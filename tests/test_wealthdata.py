"""
Tests for wealthdata compatibility module.
"""

import pytest
import pandas as pd
from engine.wealthdata import (
    set_context,
    get_context,
    clear_context,
    get_price,
    get_bars,
    bars_to_dataframe,
)
from engine.context import Context, Account, Bar


def test_set_get_clear_context():
    """Test thread-local context storage."""
    account = Account(account_id="test")
    context = Context(
        account=account,
        market_data_context=[],
        incomplete_orders=[],
        completed_orders=[],
        strategy_params={},
        exec_id="test",
        exchange="binance",
    )
    
    # Initially no context
    with pytest.raises(RuntimeError, match="Context not available"):
        get_context()
    
    # Set context
    set_context(context)
    assert get_context() == context
    
    # Clear context
    clear_context()
    with pytest.raises(RuntimeError, match="Context not available"):
        get_context()


def test_bars_to_dataframe():
    """Test Bar to DataFrame conversion."""
    bars = [
        Bar(
            open_time=1000,
            close_time=2000,
            open="100.0",
            high="110.0",
            low="90.0",
            close="105.0",
            volume="1000.0",
        ),
        Bar(
            open_time=2000,
            close_time=3000,
            open="105.0",
            high="115.0",
            low="95.0",
            close="110.0",
            volume="1100.0",
        ),
    ]
    
    df = bars_to_dataframe(bars)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']
    assert df.index[0] == 2000
    assert df.index[1] == 3000
    assert df.iloc[0]['close'] == 105.0
    assert df.iloc[1]['close'] == 110.0


def test_bars_to_dataframe_empty():
    """Test empty Bar list conversion."""
    df = bars_to_dataframe([])
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']


def test_get_price():
    """Test get_price function."""
    account = Account(account_id="test")
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
        exec_id="test",
        exchange="binance",
    )
    
    set_context(context)
    
    try:
        df = get_price("BTCUSDT", count=2, frequency="1h")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'close' in df.columns
        assert df.iloc[0]['close'] == 105.0
        assert df.iloc[1]['close'] == 110.0
    finally:
        clear_context()


def test_get_price_no_context():
    """Test get_price without context."""
    clear_context()  # Ensure no context
    
    with pytest.raises(RuntimeError, match="Context not available"):
        get_price("BTCUSDT", count=20, frequency="1h")


def test_get_bars():
    """Test get_bars function (alias for get_price)."""
    account = Account(account_id="test")
    market_data = [{
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
    }]
    
    context = Context(
        account=account,
        market_data_context=market_data,
        incomplete_orders=[],
        completed_orders=[],
        strategy_params={},
        exec_id="test",
        exchange="binance",
    )
    
    set_context(context)
    
    try:
        df = get_bars("BTCUSDT", count=1, frequency="1h")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['close'] == 105.0
    finally:
        clear_context()

