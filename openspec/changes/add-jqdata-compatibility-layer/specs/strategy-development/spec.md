## ADDED Requirements

### Requirement: jqdata Module Compatibility Layer

The framework SHALL provide a `jqdata`/`jqdatasdk` compatibility module that enables JoinQuant users to directly copy-paste strategy code with minimal modifications.

The compatibility module SHALL:
- Support module-level API calls (e.g., `jqdatasdk.get_price()`)
- Automatically convert Bar objects to pandas DataFrame format
- Access Context object via thread-local storage
- Map JoinQuant APIs to framework's data access methods

#### Scenario: Strategy uses jqdatasdk.get_price()
- **WHEN** a strategy imports `jqdata` (or `jqdatasdk`) and calls `jqdata.get_price(symbol, count=20, frequency='1h')`
- **THEN** the function SHALL access the current execution Context from thread-local storage
- **AND** call `context.history(symbol, 20, '1h')` internally
- **AND** convert the returned Bar objects to pandas DataFrame
- **AND** return DataFrame with columns: open, high, low, close, volume, indexed by time
- **AND** if Context is not available, raise RuntimeError with clear message

#### Scenario: Strategy uses jqdatasdk.get_bars()
- **WHEN** a strategy calls `jqdata.get_bars(symbol, count=20, frequency='1h')`
- **THEN** it SHALL behave identically to `get_price()`
- **AND** return the same DataFrame format

#### Scenario: Thread-local Context access
- **WHEN** the execution engine starts strategy execution
- **THEN** it SHALL set the Context object to thread-local storage before calling strategy functions
- **AND** clear the Context from thread-local storage after execution completes
- **AND** ensure thread-safety for concurrent strategy execution

### Requirement: DataFrame Format Compatibility

The jqdata compatibility module SHALL convert Bar objects to pandas DataFrame format matching JoinQuant's return format.

The DataFrame SHALL have:
- Columns: open, high, low, close, volume
- Time column as index (using close_time from Bar)
- Numeric values converted from string format
- Same ordering as Bar list (oldest first)

#### Scenario: DataFrame conversion
- **WHEN** `get_price()` is called
- **THEN** Bar objects SHALL be converted to DataFrame
- **AND** string prices (open, high, low, close, volume) SHALL be converted to float
- **AND** close_time SHALL be used as DataFrame index
- **AND** if `fields` parameter is provided, only specified columns SHALL be returned

### Requirement: Parameter Compatibility

The jqdata compatibility module SHALL accept JoinQuant-style parameters and handle them appropriately.

Supported parameters:
- `symbol`: Trading pair symbol
- `count`: Number of bars to retrieve
- `end_date`: End date (mapped to available data range)
- `frequency`: Time resolution (e.g., '1h', '1d')
- `fields`: Column selection (e.g., ['close', 'volume'])

Unsupported parameters (accepted but ignored):
- `fq`: Forward/backward adjustment (not applicable to crypto)
- `skip_paused`: Skip paused trading (crypto markets don't pause)

#### Scenario: Parameter handling
- **WHEN** `get_price()` is called with `count=50` but only 30 bars are available
- **THEN** it SHALL return DataFrame with 30 bars
- **AND** log a warning about data range limitation
- **AND** not raise an error

### Requirement: Data Range Awareness

The jqdata compatibility module SHALL be aware of data limitations and provide clear feedback to users.

#### Scenario: Requested data exceeds available range
- **WHEN** `get_price()` is called with `count=100` but only 50 bars are available in ExecRequest
- **THEN** it SHALL return DataFrame with available 50 bars
- **AND** log a warning message indicating data range limitation
- **AND** not raise an error (graceful degradation)

#### Scenario: Query available data range
- **WHEN** a strategy calls `jqdata.get_available_data_range(symbol, frequency)`
- **THEN** it SHALL return a tuple of (start_time, end_time, count)
- **AND** the range SHALL reflect data available in current ExecRequest

## MODIFIED Requirements

### Requirement: Strategy Execution Engine Context Management

The strategy execution engine SHALL manage Context object in thread-local storage for jqdata compatibility.

#### Scenario: Engine sets Context before execution
- **WHEN** the engine starts executing a strategy
- **THEN** it SHALL set the Context object to thread-local storage
- **AND** strategy code SHALL be able to access Context via `jqdata` module functions
- **AND** after execution completes, it SHALL clear Context from thread-local storage

