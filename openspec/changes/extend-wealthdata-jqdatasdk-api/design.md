# Design: Extend wealthdata to Support More jqdatasdk APIs

## Context

The current `wealthdata` compatibility layer only supports `get_price()` and `get_bars()`, but JoinQuant's jqdatasdk provides many more APIs that are commonly used in strategies. To enable smoother migration for JoinQuant users, we need to extend `wealthdata` to support more jqdatasdk APIs.

## Goals

1. Support core jqdatasdk APIs that are commonly used in JoinQuant strategies
2. Maintain API compatibility (function signatures and return formats)
3. Adapt stock market concepts to cryptocurrency trading context
4. Provide clear documentation on adaptations and limitations

## Non-Goals

- Support all jqdatasdk APIs (focus on most commonly used ones)
- Perfect 1:1 mapping (some concepts don't translate directly)
- Real-time data updates (data is limited to ExecRequest context)

## Decisions

### Decision 1: API Selection and Prioritization

**What**: Prioritize APIs based on usage frequency and implementation complexity.

**Priority Levels**:
- **Phase 1 (High Priority)**: `get_all_securities()`, `get_trade_days()`
  - Most commonly used
  - Relatively simple to implement
  - Don't require additional data sources
  
- **Phase 2 (Medium Priority)**: `get_index_stocks()`, `get_index_weights()`
  - Commonly used for index-based strategies
  - Require definition of cryptocurrency index concept
  - May need additional data sources
  
- **Phase 3 (Low Priority)**: `get_fundamentals()`, `get_industry()`
  - Less commonly used
  - Require significant concept adaptation
  - May need additional data sources or return limited data

**Why**:
- Focus on APIs that provide the most value for migration
- Implement simpler APIs first to establish patterns
- Defer complex adaptations until core APIs are stable

### Decision 2: Concept Adaptation Strategy

**What**: Map stock market concepts to cryptocurrency trading context.

**Mapping Table**:

| jqdatasdk Concept | Stock Market | Cryptocurrency Adaptation |
|------------------|--------------|---------------------------|
| Security/Stock | Company stock (e.g., '000001.XSHE') | Trading pair (e.g., 'BTCUSDT') |
| Index | Stock index (e.g., '000300.XSHG') | Crypto index (e.g., 'BTC_INDEX') |
| Industry | Company industry classification | Crypto category (DeFi, Layer1, etc.) |
| Fundamentals | Company financial data | Trading pair basic info (market cap, 24h volume) |
| Trade Days | Trading days (exclude weekends/holidays) | Continuous 7x24 trading (all days) |

**Why**:
- Maintain API compatibility while adapting to different domain
- Provide clear mapping for users to understand adaptations
- Return reasonable defaults or empty data when concept doesn't apply

### Decision 3: Data Source Strategy

**What**: Determine data sources for each API.

**Data Sources**:
- **Context-based**: Use data from `ExecRequest.market_data_context` and `Context` object
  - `get_all_securities()`: From exchange configuration or Context
  - `get_trade_days()`: Generate time series from available data range
  
- **Configuration-based**: Use static configuration files
  - `get_index_stocks()`: Index composition from config files
  - `get_index_weights()`: Index weights from config files
  - `get_industry()`: Trading pair categories from config files
  
- **Limited/Placeholder**: Return limited data or placeholders
  - `get_fundamentals()`: Return basic trading pair info or empty DataFrame with warning

**Why**:
- Minimize external dependencies
- Use available data from execution context when possible
- Provide clear fallbacks when data is not available

### Decision 4: Return Format Compatibility

**What**: Ensure return formats match jqdatasdk as closely as possible.

**Format Standards**:
- **DataFrame**: Use pandas DataFrame for tabular data (same as jqdatasdk)
- **List**: Use Python list for simple collections
- **Dict**: Use Python dict for structured data
- **Column names**: Match jqdatasdk column names when possible
- **Index**: Use appropriate index (time, symbol, etc.) matching jqdatasdk

**Why**:
- Enable direct code migration without format conversion
- Maintain compatibility with existing pandas operations
- Reduce learning curve for migrating users

### Decision 5: Error Handling and Warnings

**What**: Provide clear feedback when APIs are used in ways that don't fully apply.

**Error Handling**:
- **RuntimeError**: When Context is not available (same as existing APIs)
- **ValueError**: When parameters are invalid
- **UserWarning**: When API is used in a way that doesn't fully apply to crypto
  - Example: `get_fundamentals()` may return limited data with warning
  - Example: `get_trade_days()` may warn that crypto trades 7x24

**Why**:
- Help users understand limitations and adaptations
- Prevent silent failures or unexpected behavior
- Guide users to appropriate alternatives when needed

## Implementation Details

### get_all_securities()

**Function Signature** (已验证与 jqdatasdk 兼容):
```python
def get_all_securities(types: List[str] = None, date: str = None) -> pd.DataFrame:
    """
    Get all securities (trading pairs) information.
    
    Compatible with jqdatasdk.get_all_securities().
    
    Args:
        types: Security types (e.g., ['stock']), ignored for crypto
        date: Date string, ignored (data is from current context)
    
    Returns:
        pandas DataFrame with columns:
        - display_name: Trading pair display name
        - name: Trading pair symbol (e.g., 'BTCUSDT')
        - start_date: Not applicable (empty or None)
        - end_date: Not applicable (empty or None, meaning still trading)
        - type: 'crypto' (all are crypto trading pairs)
        
        DataFrame index is the trading pair symbol (name)
    """
```

**Implementation**:
- **Data Source**: Extract trading pairs from `ExecRequest.market_data_context`
  - Collect all unique symbols from all market_data_context entries
  - If no data in context, return empty DataFrame with correct structure
- Return DataFrame with trading pair information matching jqdatasdk format
- Filter by symbol if needed (based on available data in context)
- **Note**: For crypto, `types` parameter is ignored (all are crypto trading pairs)

### get_trade_days()

**Function Signature** (已验证与 jqdatasdk 兼容):
```python
def get_trade_days(start_date: str = None, end_date: str = None, count: int = None) -> List[str]:
    """
    Get trade days (dates).
    
    Compatible with jqdatasdk.get_trade_days().
    
    Note: Cryptocurrency trades 7x24, so this returns all days in the range
    (including weekends, unlike stock market).
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        count: Number of days to return (if start_date not provided, 
               returns last count days from available data range)
    
    Returns:
        List of date strings (YYYY-MM-DD format), sorted in ascending order
        (earliest to latest, matching jqdatasdk behavior)
    """
```

**Implementation**:
- **Data Source**: Generate date range from `ExecRequest.market_data_context` time range
  - Extract min/max timestamps from bars in market_data_context
  - Convert to date range
- Generate date range based on parameters:
  - If `start_date` and `end_date` provided: return all dates in range
  - If only `count` provided: return last `count` days from available data range
  - If only `start_date` provided: return from start_date to end of available range
- For crypto, return ALL days (no weekends/holidays exclusion)
- Sort dates in ascending order (earliest to latest)
- Warn user that crypto trades 7x24 if needed

### get_index_stocks()

**Function Signature**:
```python
def get_index_stocks(index_symbol: str, date: str = None) -> List[str]:
    """
    Get index constituent stocks (trading pairs).
    
    Compatible with jqdatasdk.get_index_stocks().
    
    Args:
        index_symbol: Index identifier (e.g., 'BTC_INDEX', 'ETH_INDEX')
        date: Date string, ignored (current composition)
    
    Returns:
        List of trading pair symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
    """
```

**Implementation**:
- Define index composition in configuration
- Return list of trading pair symbols
- Support common crypto indices (BTC index, ETH index, etc.)

### get_index_weights()

**Function Signature**:
```python
def get_index_weights(index_symbol: str, date: str = None) -> pd.DataFrame:
    """
    Get index constituent weights.
    
    Compatible with jqdatasdk.get_index_weights().
    
    Args:
        index_symbol: Index identifier
        date: Date string, ignored (current weights)
    
    Returns:
        pandas DataFrame with columns:
        - code: Trading pair symbol
        - weight: Weight in index (0.0 to 1.0)
    """
```

**Implementation**:
- Get index weights from configuration
- Return DataFrame with symbol and weight columns

### get_fundamentals()

**Function Signature** (已验证，但需要简化适配):
```python
def get_fundamentals(valuation, statDate: str = None, statDateCount: int = None) -> pd.DataFrame:
    """
    Get fundamentals data.
    
    Compatible with jqdatasdk.get_fundamentals().
    
    Note: Financial data concept doesn't fully apply to crypto.
    jqdatasdk uses complex query objects (query(valuation).filter(...)),
    but for crypto we simplify this to return basic trading pair information
    or empty DataFrame with warning.
    
    Args:
        valuation: Query object (simplified for crypto - can accept None or basic dict)
        statDate: Stat date, ignored
        statDateCount: Stat date count, ignored
    
    Returns:
        pandas DataFrame with basic trading pair info (if available) or empty DataFrame
        Columns depend on what data is available (e.g., market_cap, volume_24h)
    """
```

**Implementation**:
- **Simplified Approach**: Accept `None` or basic dict instead of complex query object
- If `valuation` is None or simple dict, return basic trading pair information:
  - Extract symbol from valuation if possible
  - Return basic info (market cap, 24h volume, etc.) if available from context
- If data not available, return empty DataFrame with UserWarning
- Document limitations clearly in warning message
- **Phase 3 Priority**: This is complex, implement after Phase 1 and 2

### get_industry()

**Function Signature**:
```python
def get_industry(security: str, date: str = None) -> str:
    """
    Get industry (category) for a security (trading pair).
    
    Compatible with jqdatasdk.get_industry().
    
    Args:
        security: Trading pair symbol (e.g., 'BTCUSDT')
        date: Date string, ignored (current category)
    
    Returns:
        Industry/category string (e.g., 'Layer1', 'DeFi', 'Layer2')
    """
```

**Implementation**:
- Define crypto categories in configuration
- Map trading pairs to categories
- Return category string

## Risks / Trade-offs

### Risk: Concept Mismatch
**Mitigation**: Clear documentation, warnings, and reasonable defaults

### Risk: Data Source Limitations
**Mitigation**: Use available context data, provide configuration options, return placeholders when needed

### Risk: API Behavior Differences
**Mitigation**: Detailed documentation, test cases, migration guide updates

## Migration Plan

### Phase 1: Core APIs
- Implement `get_all_securities()` and `get_trade_days()`
- Update documentation

### Phase 2: Index APIs
- Implement `get_index_stocks()` and `get_index_weights()`
- Define crypto index concept

### Phase 3: Advanced APIs
- Implement `get_fundamentals()` and `get_industry()`
- Complete adaptations and error handling

