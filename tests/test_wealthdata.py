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
    get_all_securities,
    get_trade_days,
    get_index_stocks,
    get_index_weights,
    get_fundamentals,
    get_industry,
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


def test_get_all_securities():
    """Test get_all_securities function."""
    account = Account(account_id="test")
    market_data = [
        {
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
        },
        {
            "symbol": "ETHUSDT",
            "timeframe": "1h",
            "bars": [{
                "open_time": 1000,
                "close_time": 2000,
                "open": "2000.0",
                "high": "2100.0",
                "low": "1900.0",
                "close": "2050.0",
                "volume": "500.0",
            }]
        },
    ]
    
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
        df = get_all_securities()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'display_name' in df.columns
        assert 'start_date' in df.columns
        assert 'end_date' in df.columns
        assert 'type' in df.columns
        
        # Check index is 'name' (name is the index, not a column)
        assert df.index.name == 'name'
        
        # Check values
        symbols = sorted(df.index.tolist())
        assert 'BTCUSDT' in symbols
        assert 'ETHUSDT' in symbols
        
        # Check all are crypto type
        assert all(df['type'] == 'crypto')
        
        # Check display_name matches index (name)
        for symbol in symbols:
            assert df.loc[symbol, 'display_name'] == symbol
    finally:
        clear_context()


def test_get_all_securities_empty():
    """Test get_all_securities with no market data."""
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
    
    set_context(context)
    
    try:
        df = get_all_securities()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == ['display_name', 'name', 'start_date', 'end_date', 'type']
    finally:
        clear_context()


def test_get_all_securities_with_types_warning():
    """Test get_all_securities with types parameter (should warn)."""
    import warnings
    
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
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df = get_all_securities(types=['stock'])
            
            assert len(w) == 1
            assert "types parameter" in str(w[0].message).lower()
            assert isinstance(df, pd.DataFrame)
    finally:
        clear_context()


def test_get_trade_days():
    """Test get_trade_days function."""
    from datetime import datetime
    
    account = Account(account_id="test")
    # Create timestamps for Jan 1-3, 2025
    base_ts = int(datetime(2025, 1, 1, 0, 0, 0).timestamp() * 1000)
    
    market_data = [{
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "bars": [
            {
                "open_time": base_ts,
                "close_time": base_ts + 3600000,  # Jan 1, 1am
                "open": "100.0",
                "high": "110.0",
                "low": "90.0",
                "close": "105.0",
                "volume": "1000.0",
            },
            {
                "open_time": base_ts + 86400000,  # Jan 2
                "close_time": base_ts + 86400000 + 3600000,  # Jan 2, 1am
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
        # Test with date range
        days = get_trade_days('2025-01-01', '2025-01-03')
        
        assert isinstance(days, list)
        assert len(days) == 3
        assert days[0] == '2025-01-01'
        assert days[1] == '2025-01-02'
        assert days[2] == '2025-01-03'
        assert days == sorted(days)  # Should be in ascending order
        
        # Test with count
        days_count = get_trade_days(count=2)
        assert isinstance(days_count, list)
        assert len(days_count) == 2
        
        # Test with start_date only
        days_start = get_trade_days(start_date='2025-01-01')
        assert isinstance(days_start, list)
        assert len(days_start) >= 2
        assert days_start[0] == '2025-01-01'
    finally:
        clear_context()


def test_get_trade_days_no_data():
    """Test get_trade_days with no market data."""
    import warnings
    
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
    
    set_context(context)
    
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            days = get_trade_days()
            
            assert len(w) == 1
            assert "No market data" in str(w[0].message)
            assert days == []
    finally:
        clear_context()


def test_get_trade_days_no_context():
    """Test get_trade_days without context."""
    clear_context()
    
    with pytest.raises(RuntimeError, match="Context not available"):
        get_trade_days('2025-01-01', '2025-01-31')


def test_get_index_stocks():
    """Test get_index_stocks function."""
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
    
    set_context(context)
    
    try:
        # Test with known index
        stocks = get_index_stocks('BTC_INDEX')
        
        assert isinstance(stocks, list)
        assert len(stocks) > 0
        assert 'BTCUSDT' in stocks
        assert 'ETHUSDT' in stocks
        
        # Test with unknown index
        unknown_stocks = get_index_stocks('UNKNOWN_INDEX')
        assert isinstance(unknown_stocks, list)
        assert len(unknown_stocks) == 0
        
        # Test with date parameter (should warn but work)
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            stocks_with_date = get_index_stocks('BTC_INDEX', date='2025-01-01')
            assert len(w) == 1
            assert "date parameter" in str(w[0].message).lower()
            assert stocks_with_date == stocks
    finally:
        clear_context()


def test_get_index_stocks_no_context():
    """Test get_index_stocks without context."""
    clear_context()
    
    with pytest.raises(RuntimeError, match="Context not available"):
        get_index_stocks('BTC_INDEX')


def test_get_index_stocks_empty_symbol():
    """Test get_index_stocks with empty index_symbol."""
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
    
    set_context(context)
    
    try:
        with pytest.raises(ValueError, match="index_symbol parameter is required"):
            get_index_stocks('')
    finally:
        clear_context()


def test_get_index_weights():
    """Test get_index_weights function."""
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
    
    set_context(context)
    
    try:
        # Test with known index
        df = get_index_weights('BTC_INDEX')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'code' in df.columns or df.index.name == 'code'
        assert 'weight' in df.columns
        
        # Check index is 'code'
        assert df.index.name == 'code'
        
        # Check weights are in valid range
        assert all(df['weight'] >= 0.0)
        assert all(df['weight'] <= 1.0)
        
        # Check weights sum to approximately 1.0 (allowing for rounding)
        total_weight = df['weight'].sum()
        assert 0.99 <= total_weight <= 1.01  # Allow small rounding errors
        
        # Check specific symbols
        assert 'BTCUSDT' in df.index
        assert 'ETHUSDT' in df.index
        
        # Test with unknown index
        unknown_df = get_index_weights('UNKNOWN_INDEX')
        assert isinstance(unknown_df, pd.DataFrame)
        assert len(unknown_df) == 0
        assert list(unknown_df.columns) == ['code', 'weight']
        
        # Test with date parameter (should warn but work)
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df_with_date = get_index_weights('BTC_INDEX', date='2025-01-01')
            assert len(w) == 1
            assert "date parameter" in str(w[0].message).lower()
            assert len(df_with_date) == len(df)
    finally:
        clear_context()


def test_get_index_weights_no_context():
    """Test get_index_weights without context."""
    clear_context()
    
    with pytest.raises(RuntimeError, match="Context not available"):
        get_index_weights('BTC_INDEX')


def test_get_index_weights_empty_symbol():
    """Test get_index_weights with empty index_symbol."""
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
    
    set_context(context)
    
    try:
        with pytest.raises(ValueError, match="index_symbol parameter is required"):
            get_index_weights('')
    finally:
        clear_context()


def test_get_fundamentals():
    """Test get_fundamentals function."""
    import warnings
    
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
            "close": "50000.0",
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
        # Test with dict containing code
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df = get_fundamentals({'code': 'BTCUSDT'})
            
            # Should have warning about financial data
            assert len(w) >= 1
            assert any("Financial data" in str(warning.message) for warning in w)
            
            assert isinstance(df, pd.DataFrame)
            # If symbol found, should have data
            if len(df) > 0:
                assert 'code' in df.columns
                assert 'close' in df.columns
                assert 'volume' in df.columns
        
        # Test with None (should return empty DataFrame)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df_none = get_fundamentals(None)
            
            assert isinstance(df_none, pd.DataFrame)
            assert len(df_none) == 0 or len(df_none.columns) > 0
        
        # Test with unknown symbol
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df_unknown = get_fundamentals({'code': 'UNKNOWNUSDT'})
            
            assert isinstance(df_unknown, pd.DataFrame)
    finally:
        clear_context()


def test_get_fundamentals_no_context():
    """Test get_fundamentals without context."""
    clear_context()
    
    with pytest.raises(RuntimeError, match="Context not available"):
        get_fundamentals({'code': 'BTCUSDT'})


def test_get_industry():
    """Test get_industry function."""
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
    
    set_context(context)
    
    try:
        # Test with known trading pair
        category = get_industry('BTCUSDT')
        
        assert isinstance(category, str)
        assert category == 'Layer1'
        
        # Test with another known pair
        category_eth = get_industry('ETHUSDT')
        assert category_eth == 'Layer1'
        
        category_defi = get_industry('UNIUSDT')
        assert category_defi == 'DeFi'
        
        # Test with unknown trading pair
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            category_unknown = get_industry('UNKNOWNUSDT')
            
            assert len(w) == 1
            assert "Category not found" in str(w[0].message)
            assert category_unknown == ''
        
        # Test with date parameter (should warn but work)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            category_with_date = get_industry('BTCUSDT', date='2025-01-01')
            
            assert len(w) == 1
            assert "date parameter" in str(w[0].message).lower()
            assert category_with_date == 'Layer1'
    finally:
        clear_context()


def test_get_industry_no_context():
    """Test get_industry without context."""
    clear_context()
    
    with pytest.raises(RuntimeError, match="Context not available"):
        get_industry('BTCUSDT')


def test_get_industry_empty_symbol():
    """Test get_industry with empty security."""
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
    
    set_context(context)
    
    try:
        with pytest.raises(ValueError, match="security parameter is required"):
            get_industry('')
    finally:
        clear_context()

