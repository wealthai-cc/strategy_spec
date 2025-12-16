# Design: wealthdata Compatibility Layer

## Context

JoinQuant users write strategies using `jqdatasdk.get_price()` and other module-level APIs. To enable zero-code-modification migration (except import statement), we need to provide a `wealthdata` compatibility module that allows direct import and usage with the same API interface as jqdatasdk.

## Goals

1. Enable direct copy-paste of JoinQuant strategy code
2. Support module-level API calls (`wealthdata.get_price()`)
3. Automatic DataFrame conversion from Bar objects
4. Thread-safe Context access via thread-local storage
5. Minimal code changes (only import statement: `jqdatasdk` → `wealthdata`)

## Non-Goals

- Full jqdata API coverage (focus on most commonly used: get_price, get_bars)
- Real-time data streaming (event-driven snapshot data only)
- Support for all JoinQuant-specific features (focus on core trading APIs)
- Maintaining exact jqdata module name (we use `wealthdata` to avoid confusion)

## Decisions

### Decision 1: Module Name - wealthdata

**What**: Use `wealthdata` as the module name instead of `jqdata` or `jqdatasdk`.

**Why**:
- Clearly identifies as our compatibility layer
- Avoids confusion with original jqdata/jqdatasdk
- Allows users to understand they're using our framework
- Still enables zero-code modification (only import changes)

**Trade-off**: Users need to change import statement, but this is minimal and clear.

### Decision 2: Thread-Local Storage for Context Access

**What**: Use Python's `threading.local()` to store current execution Context.

**Why**:
- Enables module-level functions to access Context without passing it as parameter
- Thread-safe for concurrent strategy execution
- Clean API: `wealthdata.get_price()` works without context parameter
- Matches JoinQuant usage pattern exactly

**Implementation**:
```python
import threading

_context_local = threading.local()

def set_context(context):
    """Set current execution context (called by engine)."""
    _context_local.context = context

def get_context():
    """Get current execution context (called by wealthdata functions)."""
    return getattr(_context_local, 'context', None)

def clear_context():
    """Clear current execution context (called by engine after execution)."""
    if hasattr(_context_local, 'context'):
        delattr(_context_local, 'context')
```

### Decision 3: Module-Level API Functions

**What**: Provide `wealthdata.py` module with functions like `get_price()`, `get_bars()` that match jqdatasdk interface.

**Why**:
- Matches JoinQuant API style exactly
- Zero code modification (except import)
- Familiar API surface for users

**API Design**:
```python
# wealthdata.py
def get_price(symbol, count=None, end_date=None, frequency='1h', 
              fields=None, skip_paused=False, fq='pre'):
    """
    Get price data, compatible with jqdatasdk.get_price().
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        count: Number of bars to retrieve
        end_date: End date (limited by ExecRequest data)
        frequency: Time resolution ('1m', '5m', '1h', '1d', etc.)
        fields: Data fields to return (default: all)
        skip_paused: Ignored (not applicable for crypto)
        fq: Ignored (not applicable for crypto)
    
    Returns:
        pandas DataFrame with columns: open, high, low, close, volume
    """
    context = get_context()
    if context is None:
        raise RuntimeError("Context not available. Ensure strategy is executed by engine.")
    
    # Map to our context.history()
    bars = context.history(symbol, count or 20, frequency)
    
    # Convert to DataFrame
    return bars_to_dataframe(bars)
```

### Decision 4: DataFrame Conversion

**What**: Automatically convert Bar objects to pandas DataFrame format matching jqdata output.

**Why**:
- Maintains compatibility with existing pandas-based analysis code
- Familiar data format for JoinQuant users
- Enables direct use of pandas operations (mean, std, etc.)

**Implementation**:
```python
def bars_to_dataframe(bars):
    """Convert Bar objects to pandas DataFrame."""
    import pandas as pd
    
    data = []
    for bar in bars:
        data.append({
            'time': bar.close_time,
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': float(bar.volume),
        })
    
    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    return df
```

### Decision 5: Parameter Mapping

**What**: Map jqdatasdk parameters to our framework parameters.

**Mapping Table**:

| jqdatasdk Parameter | Our Framework | Notes |
|---------------------|---------------|-------|
| `symbol` | `symbol` | Direct mapping |
| `count` | `count` | Use directly, limit to available data |
| `end_date` | N/A | Limited by ExecRequest data range |
| `frequency` | `timeframe` | Direct mapping ('1d' → '1d', '1h' → '1h') |
| `fields` | N/A | Always return all fields (open, high, low, close, volume) |
| `skip_paused` | N/A | Not applicable for crypto |
| `fq` | N/A | Not applicable for crypto |

**Why**:
- Support most common use cases
- Clear limitations documented
- Graceful handling of unsupported parameters

## Architecture

```
Strategy Code (JoinQuant style)
    ↓
import wealthdata  # (was: import jqdatasdk)
    ↓
wealthdata.get_price() call
    ↓
wealthdata module
    ↓
get_context() from thread-local
    ↓
context.history() call
    ↓
Bar objects from ExecRequest
    ↓
bars_to_dataframe() conversion
    ↓
pandas DataFrame returned
    ↓
Strategy code continues (unchanged)
```

## API Mapping

| JoinQuant API | Our Implementation | Status |
|--------------|-------------------|--------|
| `jqdatasdk.get_price()` | `wealthdata.get_price()` → `context.history()` → DataFrame | P0 |
| `jqdatasdk.get_bars()` | `wealthdata.get_bars()` → `context.history()` → DataFrame | P0 |
| `jqdatasdk.get_fundamentals()` | Not supported initially | P1 |
| `jqdatasdk.get_trade_days()` | Not supported initially | P2 |
| `jqdatasdk.get_all_securities()` | Not supported initially | P2 |

## Migration Example

### Before (JoinQuant)

```python
import jqdatasdk

def initialize(context):
    context.symbol = '000001.XSHE'

def handle_bar(context, bar):
    df = jqdatasdk.get_price(context.symbol, count=20, frequency='1d')
    ma = df['close'].mean()
    
    if bar.close > ma:
        order_buy(context.symbol, 100)
```

### After (Our Framework - Zero Code Change)

```python
import wealthdata  # Only change: import statement

def initialize(context):
    context.symbol = 'BTCUSDT'  # Only symbol format change

def handle_bar(context, bar):
    # Code unchanged!
    df = wealthdata.get_price(context.symbol, count=20, frequency='1h')
    ma = df['close'].mean()
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)  # Only API change (order_buy → context.order_buy)
```

**Changes Summary**:
1. ✅ Import statement: `jqdatasdk` → `wealthdata` (one line)
2. ✅ Symbol format: `'000001.XSHE'` → `'BTCUSDT'` (data format change)
3. ⚠️ Order API: `order_buy()` → `context.order_buy()` (framework requirement)

**Business logic**: Completely unchanged!

## Risks / Trade-offs

### Risk: Data Range Limitations

**Issue**: Our framework provides snapshot data via ExecRequest, not unlimited historical data.

**Mitigation**:
- Document limitations clearly
- Provide `get_available_data_range()` method
- Log warnings when requested data exceeds available range
- Return available data with warning instead of error

### Risk: Performance Overhead

**Issue**: DataFrame conversion adds overhead.

**Mitigation**:
- Conversion is fast for typical data sizes (< 1000 bars)
- Provide optional parameter to return Bar objects directly
- Cache DataFrame if same data requested multiple times

### Risk: API Coverage

**Issue**: Cannot support all jqdata APIs (fundamentals, trade days, etc.).

**Mitigation**:
- Focus on most commonly used APIs (get_price, get_bars)
- Clearly document supported vs unsupported APIs
- Provide migration guide for unsupported features

### Trade-off: Module Name

**Decision**: Use `wealthdata` instead of `jqdata`/`jqdatasdk`.

**Pros**:
- Clear identification as our compatibility layer
- Avoids confusion with original jqdata
- Users understand they're using our framework

**Cons**:
- Requires import statement change (minimal)
- Users need to know about wealthdata module

**Verdict**: Acceptable trade-off for clarity and avoid confusion.

## Implementation Plan

### Phase 1: Core Module

1. Create `wealthdata.py` module structure
2. Implement thread-local storage mechanism
3. Implement `get_price()` function
4. Implement `bars_to_dataframe()` conversion
5. Add error handling and warnings

### Phase 2: Engine Integration

1. Modify engine to set Context before strategy execution
2. Modify engine to clear Context after strategy execution
3. Add error handling for missing Context

### Phase 3: Additional APIs

1. Implement `get_bars()` function
2. Add parameter validation
3. Add data range checking

### Phase 4: Documentation

1. Write migration guide
2. Create API documentation
3. Provide example strategies
4. Document limitations and workarounds

