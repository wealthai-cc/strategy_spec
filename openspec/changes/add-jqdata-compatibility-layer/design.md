# Design: jqdata Module Compatibility Layer

## Context

JoinQuant users write strategies using `jqdatasdk.get_price()` and other module-level APIs. To enable zero-code-modification migration, we need to provide a `jqdata`/`jqdatasdk` compatibility module that allows direct import and usage.

## Goals

1. Enable direct copy-paste of JoinQuant strategy code
2. Support module-level API calls (`jqdatasdk.get_price()`)
3. Automatic DataFrame conversion from Bar objects
4. Thread-safe Context access via thread-local storage
5. Minimal code changes (only import statement, or none if module name matches)

## Non-Goals

- Full jqdata API coverage (focus on most commonly used: get_price, get_bars)
- Real-time data streaming (event-driven snapshot data only)
- Support for all JoinQuant-specific features (focus on core trading APIs)

## Decisions

### Decision 1: Thread-Local Storage for Context Access

**What**: Use Python's `threading.local()` to store current execution Context.

**Why**:
- Enables module-level functions to access Context without passing it as parameter
- Thread-safe for concurrent strategy execution
- Clean API: `jqdatasdk.get_price()` works without context parameter
- Matches JoinQuant usage pattern

**Implementation**:
```python
import threading

_context_local = threading.local()

def set_context(context):
    _context_local.context = context

def get_context():
    return getattr(_context_local, 'context', None)

def clear_context():
    if hasattr(_context_local, 'context'):
        delattr(_context_local, 'context')
```

### Decision 2: Module-Level API Functions

**What**: Provide `jqdata.py` module with functions like `get_price()`, `get_bars()`.

**Why**:
- Matches JoinQuant API style exactly
- Zero code modification (except import)
- Familiar API surface for users

**API Design**:
```python
# jqdata.py
def get_price(symbol, count=None, end_date=None, frequency='1h', 
              fields=None, skip_paused=False, fq='pre'):
    context = get_context()
    if context is None:
        raise RuntimeError("Context not available")
    
    bars = context.history(symbol, count or 20, frequency)
    return bars_to_dataframe(bars, fields)
```

### Decision 3: DataFrame Conversion

**What**: Automatically convert Bar objects to pandas DataFrame.

**Why**:
- JoinQuant returns DataFrame format
- Users expect DataFrame for analysis
- Enables direct use of pandas operations

**Conversion**:
```python
def bars_to_dataframe(bars, fields=None):
    data = [{
        'time': bar.close_time,
        'open': float(bar.open),
        'high': float(bar.high),
        'low': float(bar.low),
        'close': float(bar.close),
        'volume': float(bar.volume),
    } for bar in bars]
    
    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    
    if fields:
        df = df[fields]
    
    return df
```

### Decision 4: Engine Integration

**What**: Engine sets Context to thread-local before execution, clears after.

**Why**:
- Ensures Context is available during strategy execution
- Automatic cleanup prevents memory leaks
- Thread-safe for concurrent execution

**Implementation**:
```python
class StrategyExecutionEngine:
    def execute(self, exec_request):
        context = self._build_context(exec_request)
        try:
            set_context(context)
            # Execute strategy
            # jqdatasdk.get_price() can now access context
        finally:
            clear_context()
```

### Decision 5: Parameter Compatibility

**What**: Accept JoinQuant parameters but handle gracefully for unsupported features.

**Why**:
- Allows direct copy-paste without parameter changes
- Graceful degradation for unsupported features
- Clear error messages for critical mismatches

**Handling**:
- `fq` (复权): Accept but ignore, log warning
- `skip_paused`: Accept but ignore (crypto markets don't pause)
- `end_date`: Map to available data range
- `count`: Use directly, limit to available data

## Architecture

```
Strategy Code
    ↓
import jqdatasdk  (our compatibility module)
    ↓
jqdatasdk.get_price() call
    ↓
jqdata module
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
Strategy code continues
```

## API Mapping

| JoinQuant API | Our Implementation | Status |
|--------------|-------------------|--------|
| `jqdatasdk.get_price()` | `jqdata.get_price()` → `context.history()` → DataFrame | P0 |
| `jqdatasdk.get_bars()` | `jqdata.get_bars()` → `context.history()` → DataFrame | P0 |
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
import jqdata  # or jqdatasdk, if we use same name

def initialize(context):
    context.symbol = 'BTCUSDT'  # Only symbol format change

def handle_bar(context, bar):
    # Code unchanged!
    df = jqdata.get_price(context.symbol, count=20, frequency='1d')
    ma = df['close'].mean()
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)  # Only API change
```

**Changes**:
1. Import statement: `jqdatasdk` → `jqdata` (or keep same if module name matches)
2. Symbol format: `'000001.XSHE'` → `'BTCUSDT'`
3. Order API: `order_buy()` → `context.order_buy()`

**Business logic**: Completely unchanged!

## Risks / Trade-offs

### Risk: Data Range Limitations

**Issue**: Our framework provides snapshot data via ExecRequest, not unlimited historical data.

**Mitigation**: 
- Document limitations clearly
- Log warnings when requested data exceeds available range
- Provide `get_available_data_range()` method

### Risk: Performance Overhead

**Issue**: DataFrame conversion adds overhead.

**Mitigation**:
- Conversion is lightweight (simple list comprehension)
- Consider caching if same data requested multiple times
- Allow direct Bar access via `context.history()` for performance-critical code

### Risk: API Coverage

**Issue**: Not all jqdata APIs can be supported.

**Mitigation**:
- Prioritize most commonly used APIs (get_price, get_bars)
- Provide clear error messages for unsupported APIs
- Document supported vs unsupported APIs

### Trade-off: Simplicity vs Completeness

**Decision**: Prioritize simplicity and common use cases over complete API coverage.

## Implementation Plan

### Phase 1: Core Implementation

1. Create `context_local.py` with thread-local storage
2. Create `jqdata.py` module with `get_price()` and `get_bars()`
3. Implement DataFrame conversion
4. Integrate with engine (set/clear context)
5. Add unit tests

### Phase 2: Documentation

1. Write zero-code migration guide
2. Create API mapping documentation
3. Provide migration examples
4. Document limitations and differences

### Phase 3: Extended APIs (Optional)

1. Add `get_fundamentals()` if needed
2. Add other commonly used APIs
3. Improve parameter compatibility

