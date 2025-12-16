# Design: JoinQuant Compatibility Layer

## Context

JoinQuant uses `jqdata` (jqdatasdk) for data access, providing APIs like `get_price()`, `get_bars()`, etc. Our framework uses `context.history()` with a different API style. To enable smooth migration for JoinQuant users, we need a compatibility layer.

## Goals

1. Enable JoinQuant strategies to run with minimal code changes
2. Provide jqdata-style APIs on Context object
3. Support pandas DataFrame format for data compatibility
4. Maintain backward compatibility with existing APIs

## Non-Goals

- Full jqdata API coverage (focus on most commonly used APIs)
- Real-time data streaming (event-driven only)
- Support for all jqdata features (focus on core trading APIs)

## Decisions

### Decision 1: API Mapping Strategy

**What**: Map jqdata-style APIs to our data access methods.

**Mapping Table**:

| JoinQuant API | Our Framework | Notes |
|--------------|---------------|-------|
| `jqdatasdk.get_price()` | `context.get_price()` | Returns DataFrame |
| `jqdatasdk.get_bars()` | `context.get_bars()` | Returns DataFrame |
| `context.current_bar()` | `context.current_bar` | Direct access |
| `context.account` | `context.account` | Already compatible |
| `order_buy()` | `context.order_buy()` | Already compatible |
| `order_sell()` | `context.order_sell()` | Already compatible |

**Why**:
- Minimal code changes for users
- Familiar API surface
- Easy to understand and migrate

**Implementation**:
```python
class Context:
    def get_price(self, symbol, count=None, end_date=None, frequency='1h'):
        """
        Get price data in JoinQuant style.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            count: Number of bars (default: all available)
            end_date: End date (ignored, uses current bar)
            frequency: Timeframe (e.g., '1h', '1d')
        
        Returns:
            pandas DataFrame with columns: open, high, low, close, volume
        """
        bars = self.history(symbol, count or 100, frequency)
        return self._bars_to_dataframe(bars)
    
    def get_bars(self, symbol, count=None, end_date=None, frequency='1h'):
        """Alias for get_price, returns same DataFrame format."""
        return self.get_price(symbol, count, end_date, frequency)
```

### Decision 2: DataFrame Conversion

**What**: Convert Bar objects to pandas DataFrame format.

**Why**:
- JoinQuant strategies expect DataFrame format
- Enables use of existing pandas analysis code
- Familiar data structure for quant developers

**Implementation**:
```python
def _bars_to_dataframe(self, bars: List[Bar]) -> pd.DataFrame:
    """Convert Bar objects to pandas DataFrame."""
    import pandas as pd
    
    data = {
        'open': [float(b.open) for b in bars],
        'high': [float(b.high) for b in bars],
        'low': [float(b.low) for b in bars],
        'close': [float(b.close) for b in bars],
        'volume': [float(b.volume) for b in bars],
        'time': [b.close_time for b in bars],
    }
    
    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    return df
```

### Decision 3: Data Range Limitation Handling

**What**: Clearly document and handle data range limitations.

**Why**:
- Our framework provides data via ExecRequest (limited scope)
- JoinQuant allows querying arbitrary historical data
- Users need to understand this difference

**Approach**:
1. Document limitation in API docstrings
2. Log warning when requested data exceeds available
3. Return available data with warning
4. Provide `context.get_available_data_range()` method

**Implementation**:
```python
def get_price(self, symbol, count=None, end_date=None, frequency='1h'):
    bars = self.history(symbol, count or 100, frequency)
    
    if count and len(bars) < count:
        import warnings
        warnings.warn(
            f"Requested {count} bars, but only {len(bars)} available. "
            f"Data range is limited by ExecRequest."
        )
    
    return self._bars_to_dataframe(bars)
```

### Decision 4: Optional pandas Dependency

**What**: Make pandas an optional dependency with graceful fallback.

**Why**:
- Not all strategies need DataFrame format
- Reduces dependency overhead
- Maintains framework simplicity

**Approach**:
- Check if pandas is available
- If not available, raise helpful error message
- Document pandas as optional dependency

**Implementation**:
```python
def _bars_to_dataframe(self, bars: List[Bar]) -> pd.DataFrame:
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame conversion. "
            "Install with: pip install pandas"
        )
    # ... conversion code
```

### Decision 5: Backward Compatibility

**What**: Keep existing APIs unchanged, add new APIs as extensions.

**Why**:
- Existing strategies continue to work
- No breaking changes
- Gradual migration path

**Approach**:
- `context.history()` remains unchanged
- New methods added alongside
- Both APIs available simultaneously

## API Design

### New Context Methods

```python
class Context:
    # Existing method (unchanged)
    def history(self, symbol: str, count: int, timeframe: str) -> List[Bar]:
        """Get historical bar data (existing API)."""
        pass
    
    # New JoinQuant-style methods
    def get_price(
        self,
        symbol: str,
        count: int = None,
        end_date: str = None,
        frequency: str = '1h'
    ) -> pd.DataFrame:
        """
        Get price data in JoinQuant style.
        
        Returns pandas DataFrame with columns: open, high, low, close, volume
        """
        pass
    
    def get_bars(
        self,
        symbol: str,
        count: int = None,
        end_date: str = None,
        frequency: str = '1h'
    ) -> pd.DataFrame:
        """Alias for get_price."""
        return self.get_price(symbol, count, end_date, frequency)
    
    def get_available_data_range(self, symbol: str, frequency: str) -> tuple:
        """
        Get available data range for symbol.
        
        Returns:
            (start_time, end_time, count) tuple
        """
        pass
```

## Migration Examples

### Before (JoinQuant)

```python
import jqdatasdk

def initialize(context):
    context.symbol = '000001.XSHE'

def handle_bar(context, bar):
    # Get price data
    df = jqdatasdk.get_price(context.symbol, count=20, frequency='1d')
    
    # Calculate MA
    ma = df['close'].mean()
    
    # Trading logic
    if bar.close > ma:
        order_buy(context.symbol, 100)
```

### After (Our Framework - Option 1: Minimal Change)

```python
def initialize(context):
    context.symbol = 'BTCUSDT'  # Changed symbol format

def handle_bar(context, bar):
    # Use context.get_price() instead of jqdatasdk.get_price()
    df = context.get_price(context.symbol, count=20, frequency='1d')
    
    # Rest of code unchanged
    ma = df['close'].mean()
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)  # Changed order API
```

### After (Our Framework - Option 2: Native API)

```python
def initialize(context):
    context.symbol = 'BTCUSDT'

def handle_bar(context, bar):
    # Use native API
    bars = context.history(context.symbol, 20, '1d')
    
    # Calculate MA manually
    ma = sum(float(b.close) for b in bars) / len(bars)
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)
```

## Risks / Trade-offs

### Risk: Data Range Limitation

**Mitigation**: 
- Clear documentation
- Runtime warnings
- Provide `get_available_data_range()` method

### Risk: Performance Overhead

**Mitigation**:
- DataFrame conversion is lightweight
- Optional dependency
- Cache conversion results if needed

### Trade-off: API Complexity vs Compatibility

**Decision**: Add compatibility layer as optional extension, keep core API simple.

## Implementation Plan

### Phase 1: Core Compatibility APIs
- Add `get_price()` and `get_bars()` to Context
- Implement DataFrame conversion
- Add data range query method

### Phase 2: jqdata Module Compatibility Layer
- Create `jqdata.py` or `jqdatasdk.py` module
- Implement thread-local Context storage
- Map `jqdatasdk.get_price()` to `context.get_price()`
- Handle module-level function calls

### Phase 3: Documentation
- Write migration guide (zero-code-change approach)
- Create API comparison table
- Provide migration examples

### Phase 4: Migration Tools (Optional)
- Code conversion script (auto-replace import)
- Migration checklist
- Validation tools

## Decision 6: jqdata Module Implementation

**What**: Create a `jqdata` module that provides JoinQuant-compatible APIs at module level.

**Why**:
- Enable zero-code-change migration
- Users can directly copy JoinQuant code
- Only need to change `import jqdatasdk` to `import jqdata`

**Implementation**:
```python
# jqdata.py (or jqdatasdk.py)
import threading
from typing import Optional

# Thread-local storage for current Context
_context_local = threading.local()

def set_context(context):
    """Set current execution context (called by engine)."""
    _context_local.context = context

def get_context() -> Optional['Context']:
    """Get current execution context."""
    return getattr(_context_local, 'context', None)

def get_price(security, count=None, end_date=None, frequency='1h', fields=None):
    """
    Get price data (JoinQuant-compatible API).
    
    Args:
        security: Symbol (e.g., 'BTCUSDT')
        count: Number of bars
        end_date: End date (ignored)
        frequency: Timeframe (e.g., '1h', '1d')
        fields: Fields to retrieve (ignored, returns all)
    
    Returns:
        pandas DataFrame
    """
    context = get_context()
    if context is None:
        raise RuntimeError("No context available. This function must be called within strategy execution.")
    
    return context.get_price(security, count, end_date, frequency)

def get_bars(security, count=None, end_date=None, frequency='1h'):
    """Alias for get_price."""
    return get_price(security, count, end_date, frequency)

# Export all functions
__all__ = ['get_price', 'get_bars', 'set_context', 'get_context']
```

**Engine Integration**:
```python
# In engine.py, before executing strategy
import jqdata
jqdata.set_context(context)

# Execute strategy (strategy can use jqdatasdk.get_price())
result = strategy_function(context, bar)

# After execution, cleanup
jqdata.set_context(None)
```

**Strategy Usage**:
```python
# Strategy code (copied from JoinQuant, only import changed)
import jqdata  # Changed from: import jqdatasdk

def initialize(context):
    context.symbol = 'BTCUSDT'

def handle_bar(context, bar):
    # Original JoinQuant code, no changes needed
    df = jqdata.get_price(context.symbol, count=20, frequency='1h')
    ma = df['close'].mean()
    
    if float(bar.close) > ma:
        order_buy(context.symbol, 0.1)
```

