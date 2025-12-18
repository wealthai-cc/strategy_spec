# Strategy Engine Spec - JoinQuant Compatibility Enhancements

## ADDED Requirements

### Requirement: Global Variable Injection

The strategy loader SHALL inject a `g` global variable object into each strategy module's namespace during loading, compatible with JoinQuant's global variable support.

#### Scenario: Injecting g object
- **WHEN** a strategy file is loaded by the StrategyLoader
- **THEN** the loader SHALL create a `g` object and inject it into the strategy module
- **AND** the strategy SHALL be able to access `g` without explicit import

#### Scenario: g object isolation
- **WHEN** the same strategy file is loaded multiple times (different instances)
- **THEN** each instance SHALL have its own independent `g` object
- **AND** changes to `g` in one instance SHALL NOT affect other instances

### Requirement: Log Module Injection

The strategy loader SHALL inject a `log` module object into each strategy module's namespace during loading, compatible with JoinQuant's logging interface.

#### Scenario: Injecting log module
- **WHEN** a strategy file is loaded by the StrategyLoader
- **THEN** the loader SHALL inject a `log` object with `info()`, `warn()`, `error()`, `debug()`, and `set_level()` methods
- **AND** the strategy SHALL be able to access `log` without explicit import

### Requirement: Scheduled Function Registration

The engine SHALL support registration of scheduled functions via `run_daily()`, and SHALL call these functions at appropriate times during strategy execution.

#### Scenario: Registering scheduled functions
- **WHEN** a strategy calls `run_daily(func, time='before_open', reference_security='BTCUSDT')` during `initialize()`
- **THEN** the engine SHALL register the function for execution at the specified time
- **AND** SHALL store the function, time, and reference security information

#### Scenario: Executing scheduled functions
- **WHEN** the engine calls `before_trading(context)` and the current execution context matches a registered scheduled function's time
- **THEN** the engine SHALL call the registered function with the `context` parameter
- **AND** SHALL call all matching scheduled functions in registration order

#### Scenario: Time matching logic
- **WHEN** a scheduled function is registered with `time='before_open'`
- **THEN** the engine SHALL call it during `before_trading` if the current time is before market open
- **WHEN** a scheduled function is registered with `time='open'`
- **THEN** the engine SHALL call it during `before_trading` if the current time is at market open
- **WHEN** a scheduled function is registered with `time='after_close'`
- **THEN** the engine SHALL call it during `before_trading` if the current time is after market close

### Requirement: Order Function Injection

The strategy loader SHALL inject `order_value()` and `order_target()` functions into each strategy module's namespace during loading, compatible with JoinQuant's order APIs.

#### Scenario: Injecting order functions
- **WHEN** a strategy file is loaded by the StrategyLoader
- **THEN** the loader SHALL inject `order_value` and `order_target` functions
- **AND** the strategy SHALL be able to call these functions without explicit import

#### Scenario: Order function context access
- **WHEN** `order_value()` or `order_target()` is called
- **THEN** the function SHALL access the current Context via thread-local storage
- **AND** SHALL use the Context to place orders and query positions

### Requirement: Config Function Injection

The strategy loader SHALL inject simplified config functions (`set_benchmark()`, `set_option()`, `set_order_cost()`) into each strategy module's namespace, compatible with JoinQuant's config APIs.

#### Scenario: Injecting config functions
- **WHEN** a strategy file is loaded by the StrategyLoader
- **THEN** the loader SHALL inject `set_benchmark`, `set_option`, and `set_order_cost` functions
- **AND** these functions SHALL accept parameters and store them (simplified implementation, may not affect execution)

## MODIFIED Requirements

### Requirement: Strategy Loading Process

The strategy loading process SHALL inject JoinQuant-compatible objects and functions into the strategy module namespace:

- `g`: Global variable object
- `log`: Logging module
- `run_daily`: Scheduled function registration
- `order_value`, `order_target`: Order functions
- `set_benchmark`, `set_option`, `set_order_cost`: Config functions

#### Scenario: Complete injection
- **WHEN** a strategy file is loaded
- **THEN** all JoinQuant-compatible objects and functions SHALL be injected
- **AND** the strategy SHALL be able to use them without explicit imports
- **AND** existing strategies without these dependencies SHALL continue to work

### Requirement: Lifecycle Management

The lifecycle manager SHALL check for and execute registered scheduled functions during `before_trading()` calls.

#### Scenario: Executing scheduled functions in before_trading
- **WHEN** the lifecycle manager calls `before_trading(context)`
- **THEN** it SHALL check for registered scheduled functions matching the current time
- **AND** SHALL call all matching scheduled functions with the `context` parameter
- **AND** SHALL call them before the strategy's own `before_trading()` function (if exists)

### Requirement: Context Building

The Context building process SHALL populate additional JoinQuant-compatible attributes:

- `context.current_dt`: datetime object from `current_bar.close_time`
- `context.portfolio.available_cash`: calculated from account balances
- `context.portfolio.positions_value`: calculated from positions and market prices
- `context.portfolio.positions`: dictionary-style access to positions

#### Scenario: Building compatible context
- **WHEN** the engine builds a Context object from ExecRequest
- **THEN** it SHALL populate all JoinQuant-compatible attributes
- **AND** SHALL maintain backward compatibility with existing Context usage
- **AND** SHALL handle cases where required data is missing (e.g., `current_bar` is None)

