## ADDED Requirements

### Requirement: JoinQuant-style Data Access APIs

The Context object SHALL provide JoinQuant-compatible data access methods to enable smooth migration from JoinQuant platform.

The Context object SHALL support:
- `get_price(symbol, count, end_date, frequency)` - Get price data as pandas DataFrame
- `get_bars(symbol, count, end_date, frequency)` - Alias for get_price
- `get_available_data_range(symbol, frequency)` - Query available data range

These methods SHALL map to the existing `history()` method internally, converting Bar objects to DataFrame format.

#### Scenario: Strategy uses get_price() API
- **WHEN** a strategy calls `context.get_price('BTCUSDT', count=20, frequency='1h')`
- **THEN** the method SHALL return a pandas DataFrame with columns: open, high, low, close, volume
- **AND** the DataFrame SHALL be indexed by time
- **AND** the data SHALL come from `context.history()` method
- **AND** if requested count exceeds available data, a warning SHALL be logged

#### Scenario: Strategy uses get_bars() API
- **WHEN** a strategy calls `context.get_bars('BTCUSDT', count=20, frequency='1h')`
- **THEN** it SHALL behave identically to `get_price()`
- **AND** return the same DataFrame format

#### Scenario: Query available data range
- **WHEN** a strategy calls `context.get_available_data_range('BTCUSDT', '1h')`
- **THEN** it SHALL return a tuple of (start_time, end_time, count)
- **AND** the range SHALL reflect data available in current ExecRequest

### Requirement: DataFrame Format Compatibility

The Context object SHALL convert Bar objects to pandas DataFrame format when using JoinQuant-style APIs.

The DataFrame SHALL have:
- Columns: open, high, low, close, volume, time
- Time column as index
- Numeric values converted from string format
- Same ordering as Bar list (oldest first)

#### Scenario: DataFrame conversion
- **WHEN** `get_price()` is called
- **THEN** Bar objects SHALL be converted to DataFrame
- **AND** string prices SHALL be converted to float
- **AND** time SHALL be set as index
- **AND** columns SHALL match expected format

### Requirement: Data Range Limitation Handling

The framework SHALL clearly communicate data range limitations to users.

When requested data count exceeds available data:
- A warning SHALL be logged
- Available data SHALL be returned
- The limitation SHALL be documented in API docstrings

#### Scenario: Request exceeds available data
- **WHEN** strategy requests 100 bars but only 50 are available
- **THEN** a warning SHALL be logged
- **AND** 50 bars SHALL be returned
- **AND** no error SHALL be raised

### Requirement: Backward Compatibility

The existing `history()` method and other Context APIs SHALL remain unchanged.

New JoinQuant-style APIs SHALL be added as extensions, not replacements.

#### Scenario: Existing strategy continues to work
- **WHEN** an existing strategy uses `context.history()`
- **THEN** it SHALL continue to work without modification
- **AND** behavior SHALL remain identical

### Requirement: Optional pandas Dependency

pandas SHALL be an optional dependency for the framework.

When pandas is not available:
- JoinQuant-style APIs SHALL raise ImportError with helpful message
- Existing APIs (history) SHALL continue to work
- Documentation SHALL clearly state pandas requirement

#### Scenario: pandas not installed
- **WHEN** strategy calls `context.get_price()` and pandas is not installed
- **THEN** ImportError SHALL be raised with message: "pandas is required for DataFrame conversion. Install with: pip install pandas"
- **AND** existing `context.history()` SHALL continue to work

## MODIFIED Requirements

### Requirement: Context Object Data Access

The Context object SHALL support both native and JoinQuant-style data access methods.

**Existing behavior** (unchanged):
- `context.history(symbol, count, timeframe)` returns List[Bar]

**New behavior** (added):
- `context.get_price(symbol, count, end_date, frequency)` returns pd.DataFrame
- `context.get_bars(symbol, count, end_date, frequency)` returns pd.DataFrame

Both methods SHALL access the same underlying data from ExecRequest.

