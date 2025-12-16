## ADDED Requirements

### Requirement: wealthdata Compatibility Module
The framework SHALL provide a `wealthdata` compatibility module that enables JoinQuant users to migrate strategies with minimal code changes.

The `wealthdata` module SHALL:
- Provide module-level API functions matching jqdatasdk interface
- Support `get_price()` and `get_bars()` functions
- Return pandas DataFrame format (compatible with jqdata output)
- Access current execution Context via thread-local storage
- Enable zero-code modification migration (only import statement change)

#### Scenario: User migrates JoinQuant strategy
- **WHEN** a user copies JoinQuant strategy code
- **AND** changes `import jqdatasdk` to `import wealthdata`
- **THEN** the strategy SHALL execute successfully
- **AND** `wealthdata.get_price()` calls SHALL work without modification
- **AND** returned data SHALL be pandas DataFrame format
- **AND** all business logic code SHALL remain unchanged

#### Scenario: wealthdata module accesses Context
- **WHEN** strategy code calls `wealthdata.get_price()`
- **THEN** the module SHALL access current execution Context via thread-local storage
- **AND** if Context is not available, SHALL raise RuntimeError with clear message
- **AND** the Context SHALL be set by execution engine before strategy execution
- **AND** the Context SHALL be cleared by execution engine after strategy execution

#### Scenario: DataFrame conversion
- **WHEN** `wealthdata.get_price()` is called
- **THEN** the function SHALL call `context.history()` to get Bar objects
- **AND** Bar objects SHALL be converted to pandas DataFrame
- **AND** DataFrame SHALL have columns: open, high, low, close, volume
- **AND** DataFrame index SHALL be time (close_time from Bar objects)

### Requirement: Thread-Local Context Storage
The execution engine SHALL provide thread-local storage mechanism for Context access.

The engine SHALL:
- Set current execution Context to thread-local storage before strategy execution
- Clear Context from thread-local storage after strategy execution
- Support concurrent strategy execution (each thread has independent Context)
- Handle exceptions and ensure Context is always cleared

#### Scenario: Engine sets Context before execution
- **WHEN** engine executes a strategy
- **THEN** it SHALL set the Context object to thread-local storage
- **AND** wealthdata module functions SHALL be able to access this Context
- **AND** Context SHALL be available for the entire strategy execution

#### Scenario: Engine clears Context after execution
- **WHEN** strategy execution completes (success or failure)
- **THEN** engine SHALL clear Context from thread-local storage
- **AND** subsequent calls to wealthdata functions SHALL raise RuntimeError
- **AND** Context SHALL not leak between executions

### Requirement: API Compatibility
The `wealthdata` module SHALL provide API functions compatible with jqdatasdk.

The module SHALL support:
- `get_price(symbol, count=None, end_date=None, frequency='1h', fields=None, skip_paused=False, fq='pre')`
- `get_bars(symbol, count=None, end_date=None, frequency='1h', fields=None, skip_paused=False, fq='pre')`

Parameters SHALL be mapped as follows:
- `symbol` → direct mapping to context.history() symbol parameter
- `count` → direct mapping to context.history() count parameter
- `frequency` → direct mapping to context.history() timeframe parameter
- `end_date` → limited by ExecRequest data range (may be ignored with warning)
- `fields`, `skip_paused`, `fq` → ignored (not applicable for crypto trading)

#### Scenario: get_price with count parameter
- **WHEN** user calls `wealthdata.get_price('BTCUSDT', count=20, frequency='1h')`
- **THEN** function SHALL call `context.history('BTCUSDT', 20, '1h')`
- **AND** return pandas DataFrame with 20 rows (or available data if less)
- **AND** DataFrame SHALL have correct time index and OHLCV columns

#### Scenario: get_price with unsupported parameters
- **WHEN** user calls `wealthdata.get_price()` with `end_date` parameter
- **THEN** function SHALL log warning if end_date exceeds available data range
- **AND** function SHALL return available data (not raise error)
- **AND** function SHALL ignore `skip_paused` and `fq` parameters silently

## MODIFIED Requirements

### Requirement: Strategy Development with wealthdata
Strategies MAY use `wealthdata` module for data access, in addition to existing `context.history()` method.

Strategies using wealthdata SHALL:
- Import `wealthdata` module (instead of `jqdatasdk`)
- Use module-level functions (`wealthdata.get_price()`) instead of context methods
- Receive pandas DataFrame format (instead of Bar object list)
- Work with existing pandas-based analysis code without modification

#### Scenario: Strategy uses wealthdata
- **WHEN** strategy imports `wealthdata` module
- **AND** calls `wealthdata.get_price()` in lifecycle functions
- **THEN** function SHALL access Context via thread-local storage
- **AND** return DataFrame compatible with jqdata format
- **AND** strategy business logic SHALL work without modification

