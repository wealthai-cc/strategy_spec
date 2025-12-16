## MODIFIED Requirements

### Requirement: Trading Rule Query for Binance
The `get_trading_rule()` function SHALL be designed specifically for Binance exchange.

The broker parameter SHALL always be "binance". The function SHALL query Binance-specific trading rules, including:
- Binance minimum order quantities
- Binance price precision requirements
- Binance quantity step sizes
- Binance maximum leverage limits
- Binance-specific trading constraints

#### Scenario: Query Binance trading rules
- **WHEN** `get_trading_rule("binance", "BTCUSDT")` is called
- **THEN** the function SHALL return Binance-specific trading rules for the symbol
- **AND** the rules SHALL reflect Binance exchange constraints

#### Scenario: Invalid broker parameter
- **WHEN** `get_trading_rule()` is called with a broker parameter other than "binance"
- **THEN** the function SHALL return `NotFoundError` or a validation error
- **AND** the error message SHALL indicate that only "binance" is supported

### Requirement: Commission Rate Query for Binance
The `get_commission_rates()` function SHALL be designed specifically for Binance exchange.

The broker parameter SHALL always be "binance". The function SHALL return Binance-specific commission rates, including:
- Binance Maker fee rates
- Binance Taker fee rates
- Binance VIP tier rates (if applicable)
- Binance-specific fee structures

#### Scenario: Query Binance commission rates
- **WHEN** `get_commission_rates("binance", "BTCUSDT")` is called
- **THEN** the function SHALL return Binance-specific commission rates
- **AND** the rates SHALL reflect actual Binance trading fees

#### Scenario: Invalid broker parameter
- **WHEN** `get_commission_rates()` is called with a broker parameter other than "binance"
- **THEN** the function SHALL return `NotFoundError` or a validation error
- **AND** the error message SHALL indicate that only "binance" is supported

## ADDED Requirements

### Requirement: Binance-Specific Constraints
The Python SDK SHALL document and enforce Binance-specific constraints, including:
- Binance symbol format (e.g., "BTCUSDT", not "BTC/USDT")
- Binance order type support (Market, Limit, Stop Market, Stop Limit)
- Binance time-in-force options (GTC, IOC, FOK)
- Binance precision requirements for price and quantity
- Binance API rate limits and constraints

#### Scenario: Binance symbol format validation
- **WHEN** a trading rule is queried for a symbol
- **THEN** the symbol format SHALL match Binance conventions (e.g., "BTCUSDT")
- **AND** invalid formats SHALL return appropriate errors

#### Scenario: Binance order type support
- **WHEN** creating orders through the strategy framework
- **THEN** only Binance-supported order types SHALL be used
- **AND** the system SHALL validate order types against Binance capabilities

