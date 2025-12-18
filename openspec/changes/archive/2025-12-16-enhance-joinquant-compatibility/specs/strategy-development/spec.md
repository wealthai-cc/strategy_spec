# Strategy Development Spec - JoinQuant Compatibility Enhancements

## ADDED Requirements

### Requirement: Global Variable Support (g)

The framework SHALL provide a global variable object `g` that strategies can use to store strategy-level state, compatible with JoinQuant's `g` object.

#### Scenario: Using global variable in strategy
- **WHEN** a strategy assigns a value to `g.security = 'BTCUSDT'`
- **THEN** the value SHALL be accessible in other functions within the same strategy file
- **AND** the `g` object SHALL be injected into the strategy module namespace during loading

#### Scenario: Global variable isolation
- **WHEN** multiple strategy instances use the same strategy file
- **THEN** each instance SHALL have its own independent `g` object
- **AND** changes to `g` in one instance SHALL NOT affect other instances

### Requirement: Logging Module (log)

The framework SHALL provide a `log` module compatible with JoinQuant's logging interface, supporting standard log levels.

#### Scenario: Logging information
- **WHEN** a strategy calls `log.info('message')`
- **THEN** the message SHALL be output to standard output with `[INFO]` prefix
- **AND** the `log` object SHALL be injected into the strategy module namespace

#### Scenario: Different log levels
- **WHEN** a strategy calls `log.warn()`, `log.error()`, or `log.debug()`
- **THEN** the message SHALL be output with the corresponding prefix (`[WARN]`, `[ERROR]`, `[DEBUG]`)

#### Scenario: Log level configuration
- **WHEN** a strategy calls `log.set_level(category, level)`
- **THEN** the framework SHALL accept the call (simplified implementation, may not affect output)

### Requirement: Scheduled Function Execution (run_daily)

The framework SHALL support scheduling functions to run at specific times (before market open, market open, after market close), compatible with JoinQuant's `run_daily()` function.

#### Scenario: Registering a scheduled function
- **WHEN** a strategy calls `run_daily(before_market_open, time='before_open', reference_security='BTCUSDT')`
- **THEN** the function SHALL be registered for execution at the specified time
- **AND** the `run_daily` function SHALL be available in the strategy module namespace

#### Scenario: Executing scheduled function
- **WHEN** the engine calls `before_trading(context)` and the current time matches a registered scheduled function
- **THEN** the registered function SHALL be called with the `context` parameter
- **AND** the time matching SHALL be approximate (based on ExecRequest trigger time)

#### Scenario: Multiple scheduled functions
- **WHEN** a strategy registers multiple scheduled functions with different times
- **THEN** all matching functions SHALL be called in registration order during `before_trading`

### Requirement: Order by Value (order_value)

The framework SHALL provide an `order_value()` function that places an order for a specified value amount, compatible with JoinQuant's API. The function SHALL adapt quantity calculation based on market type.

#### Scenario: Buying by value (stock market)
- **WHEN** a strategy calls `order_value('000001.XSHE', 1000)` (buy $1000 worth of stock)
- **THEN** the framework SHALL calculate the quantity based on current price
- **AND** SHALL round the quantity to integer (stocks are traded in whole shares)
- **AND** SHALL place a buy order with the calculated quantity
- **AND** SHALL return an Order object

#### Scenario: Buying by value (cryptocurrency market)
- **WHEN** a strategy calls `order_value('BTCUSDT', 1000)` (buy $1000 worth)
- **THEN** the framework SHALL calculate the quantity based on current price
- **AND** SHALL allow fractional quantities (cryptocurrencies support decimal precision)
- **AND** SHALL place a buy order with the calculated quantity
- **AND** SHALL return an Order object

#### Scenario: Buying by value with price
- **WHEN** a strategy calls `order_value('BTCUSDT', 1000, price=50000)`
- **THEN** the framework SHALL use the specified price to calculate quantity
- **AND** SHALL place a limit order with the calculated quantity and price

### Requirement: Order to Target Position (order_target)

The framework SHALL provide an `order_target()` function that adjusts position to a target quantity, compatible with JoinQuant's API. The function SHALL adapt quantity calculation based on market type.

#### Scenario: Increasing position to target (stock market)
- **WHEN** current position is 100 shares and strategy calls `order_target('000001.XSHE', 500)`
- **THEN** the framework SHALL place a buy order for 400 shares (500 - 100)
- **AND** SHALL ensure quantity is an integer (stocks are traded in whole shares)
- **AND** SHALL return an Order object

#### Scenario: Increasing position to target (cryptocurrency market)
- **WHEN** current position is 0.1 BTC and strategy calls `order_target('BTCUSDT', 0.5)`
- **THEN** the framework SHALL place a buy order for 0.4 BTC (0.5 - 0.1)
- **AND** SHALL allow fractional quantities
- **AND** SHALL return an Order object

#### Scenario: Decreasing position to target
- **WHEN** current position is 0.5 BTC and strategy calls `order_target('BTCUSDT', 0.1)`
- **THEN** the framework SHALL place a sell order for 0.4 BTC (0.5 - 0.1)

#### Scenario: Already at target
- **WHEN** current position is 0.5 BTC and strategy calls `order_target('BTCUSDT', 0.5)`
- **THEN** the framework SHALL NOT place any order
- **AND** SHALL return None or a no-op indicator

### Requirement: Trade History Query (get_trades)

The framework SHALL provide a `get_trades()` function that returns completed trade records, compatible with JoinQuant's API.

#### Scenario: Getting trade history
- **WHEN** a strategy calls `get_trades()`
- **THEN** the framework SHALL return a dictionary of completed trades
- **AND** each trade SHALL include symbol, price, quantity, and timestamp
- **AND** the format SHALL be compatible with JoinQuant's trade record format

### Requirement: Context Current Time (current_dt)

The Context object SHALL provide a `current_dt` attribute that represents the current time as a datetime object, compatible with JoinQuant's `context.current_dt`.

#### Scenario: Accessing current time
- **WHEN** a strategy accesses `context.current_dt`
- **THEN** the framework SHALL return a datetime object representing the current bar's time
- **AND** the datetime SHALL be calculated from `context.current_bar.close_time`

#### Scenario: Current time availability
- **WHEN** `context.current_bar` is None
- **THEN** `context.current_dt` SHALL return None or raise an appropriate exception

### Requirement: Portfolio Available Cash

The Portfolio object SHALL provide an `available_cash` attribute that represents the available cash for trading, compatible with JoinQuant's `context.portfolio.available_cash`.

#### Scenario: Accessing available cash
- **WHEN** a strategy accesses `context.portfolio.available_cash`
- **THEN** the framework SHALL return the available cash amount
- **AND** the value SHALL be calculated from `context.account.available_margin` or `context.account.balances`

### Requirement: Portfolio Positions Value

The Portfolio object SHALL provide a `positions_value` attribute that represents the total value of all positions, compatible with JoinQuant's `context.portfolio.positions_value`.

#### Scenario: Accessing positions value
- **WHEN** a strategy accesses `context.portfolio.positions_value`
- **THEN** the framework SHALL return the total market value of all positions
- **AND** the value SHALL be calculated from current positions and market prices

### Requirement: Dictionary-Style Position Access

The Portfolio object SHALL support dictionary-style access to positions using symbol as key, compatible with JoinQuant's `context.portfolio.positions[symbol]`.

#### Scenario: Accessing position by symbol
- **WHEN** a strategy accesses `context.portfolio.positions['BTCUSDT']`
- **THEN** the framework SHALL return the position object for that symbol
- **AND** SHALL return None or raise KeyError if the position does not exist

#### Scenario: Position dictionary updates
- **WHEN** positions are updated in the portfolio
- **THEN** the dictionary SHALL be kept in sync with the positions list
- **AND** SHALL support both list and dictionary access patterns

### Requirement: Market Type Detection

The framework SHALL automatically detect market type (stock market vs cryptocurrency market) based on symbol format, and SHALL apply appropriate handling logic for each market type.

#### Scenario: Detecting stock market
- **WHEN** a symbol uses JoinQuant format (e.g., `000001.XSHE`, `AAPL.US`, `00700.HK`)
- **THEN** the framework SHALL identify it as a stock market symbol
- **AND** SHALL apply stock market-specific logic (actual trading hours, trade days, etc.)

#### Scenario: Detecting cryptocurrency market
- **WHEN** a symbol uses trading pair format (e.g., `BTCUSDT`, `ETHUSDT`)
- **THEN** the framework SHALL identify it as a cryptocurrency market symbol
- **AND** SHALL apply cryptocurrency market-specific logic (7x24 trading, logical open/close times, etc.)

### Requirement: Market Type Adaptive Scheduled Execution

The `run_daily()` function SHALL adapt its time matching logic based on market type.

#### Scenario: Stock market scheduled execution
- **WHEN** a scheduled function is registered with `reference_security='000001.XSHE'` (stock market)
- **THEN** the framework SHALL match actual trading hours (e.g., 9:30 for A-shares)
- **AND** SHALL only trigger on actual trading days (excluding weekends and holidays)

#### Scenario: Cryptocurrency market scheduled execution
- **WHEN** a scheduled function is registered with `reference_security='BTCUSDT'` (cryptocurrency)
- **THEN** the framework SHALL match logical time points (e.g., 00:00 for daily start)
- **AND** SHALL trigger every day (7x24 trading, no trade day concept)

### Requirement: Market Type Adaptive Trade Days

The `get_trade_days()` function SHALL return different trade day lists based on market type.

#### Scenario: Stock market trade days
- **WHEN** `get_trade_days()` is called for a stock market symbol
- **THEN** the framework SHALL return actual trading days
- **AND** SHALL exclude weekends and holidays

#### Scenario: Cryptocurrency market trade days
- **WHEN** `get_trade_days()` is called for a cryptocurrency market symbol
- **THEN** the framework SHALL return all dates in the range
- **AND** SHALL treat every day as a trading day (7x24 trading)

## MODIFIED Requirements

### Requirement: Context Object Interface

The Context object SHALL provide additional attributes for JoinQuant compatibility:

- `current_dt`: datetime object representing current time
- `portfolio.available_cash`: available cash for trading
- `portfolio.positions_value`: total value of all positions
- `portfolio.positions`: dictionary-style access to positions

#### Scenario: Backward compatibility
- **WHEN** existing strategies access Context attributes
- **THEN** all existing attributes SHALL continue to work as before
- **AND** new attributes SHALL be optional and not required for existing strategies

### Requirement: wealthdata.get_bars() Parameter Compatibility

The `wealthdata.get_bars()` function SHALL support both `frequency` and `unit` parameters, where `unit` is an alias for `frequency`, compatible with JoinQuant's API.

#### Scenario: Using unit parameter
- **WHEN** a strategy calls `wealthdata.get_bars('BTCUSDT', count=20, unit='1d')`
- **THEN** the framework SHALL treat `unit='1d'` as equivalent to `frequency='1d'`
- **AND** SHALL return the same result as using `frequency='1d'`

#### Scenario: Parameter precedence
- **WHEN** both `frequency` and `unit` are provided
- **THEN** the framework SHALL use `frequency` if provided, otherwise use `unit`
- **AND** SHALL raise an error if both are provided with different values

