## ADDED Requirements

### Requirement: wealthdata get_all_securities API
The `wealthdata` module SHALL provide `get_all_securities()` function compatible with jqdatasdk.

The function SHALL:
- Accept optional `types` and `date` parameters (for compatibility)
- Return pandas DataFrame with trading pair information
- Include columns: `display_name`, `name`, `start_date`, `end_date`, `type`
- Get trading pairs from Context or exchange configuration
- Return empty DataFrame if no trading pairs available

#### Scenario: Get all available trading pairs
- **WHEN** a strategy calls `wealthdata.get_all_securities()`
- **THEN** the function SHALL return a DataFrame with all available trading pairs
- **AND** each row SHALL contain trading pair information (symbol, display name, type='crypto')
- **AND** the DataFrame format SHALL be compatible with jqdatasdk return format

#### Scenario: Get trading pairs with type filter
- **WHEN** a strategy calls `wealthdata.get_all_securities(types=['stock'])`
- **THEN** the function SHALL ignore the `types` parameter (not applicable for crypto)
- **AND** return all available trading pairs
- **AND** MAY issue a warning that type filtering is not applicable

### Requirement: wealthdata get_trade_days API
The `wealthdata` module SHALL provide `get_trade_days()` function compatible with jqdatasdk.

The function SHALL:
- Accept optional `start_date`, `end_date`, and `count` parameters
- Return list of date strings in 'YYYY-MM-DD' format
- Generate date range based on parameters
- Return all days in range (cryptocurrency trades 7x24, no weekends/holidays exclusion)
- Issue warning if needed to clarify 7x24 trading nature

#### Scenario: Get trade days for date range
- **WHEN** a strategy calls `wealthdata.get_trade_days(start_date='2025-01-01', end_date='2025-01-31')`
- **THEN** the function SHALL return a list of all dates from 2025-01-01 to 2025-01-31
- **AND** the list SHALL include weekends (unlike stock market)
- **AND** each date SHALL be in 'YYYY-MM-DD' format

#### Scenario: Get trade days with count
- **WHEN** a strategy calls `wealthdata.get_trade_days(count=30)`
- **THEN** the function SHALL return the last 30 days from available data range
- **AND** the list SHALL be in descending order (most recent first) or ascending order (matching jqdatasdk)

### Requirement: wealthdata get_index_stocks API
The `wealthdata` module SHALL provide `get_index_stocks()` function compatible with jqdatasdk.

The function SHALL:
- Accept `index_symbol` parameter (e.g., 'BTC_INDEX', 'ETH_INDEX')
- Accept optional `date` parameter (ignored, returns current composition)
- Return list of trading pair symbols that are constituents of the index
- Get index composition from configuration or Context
- Return empty list if index not found

#### Scenario: Get index constituents
- **WHEN** a strategy calls `wealthdata.get_index_stocks('BTC_INDEX')`
- **THEN** the function SHALL return a list of trading pair symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
- **AND** the symbols SHALL be constituents of the BTC index
- **AND** the return format SHALL match jqdatasdk (list of strings)

#### Scenario: Get index constituents for unknown index
- **WHEN** a strategy calls `wealthdata.get_index_stocks('UNKNOWN_INDEX')`
- **THEN** the function SHALL return an empty list
- **AND** MAY issue a warning that the index is not found

### Requirement: wealthdata get_index_weights API
The `wealthdata` module SHALL provide `get_index_weights()` function compatible with jqdatasdk.

The function SHALL:
- Accept `index_symbol` parameter
- Accept optional `date` parameter (ignored, returns current weights)
- Return pandas DataFrame with columns: `code` (trading pair symbol), `weight` (weight in index, 0.0 to 1.0)
- Get index weights from configuration or Context
- Return empty DataFrame if index not found

#### Scenario: Get index weights
- **WHEN** a strategy calls `wealthdata.get_index_weights('BTC_INDEX')`
- **THEN** the function SHALL return a DataFrame with trading pair symbols and their weights
- **AND** the weights SHALL sum to approximately 1.0 (allowing for rounding)
- **AND** the DataFrame format SHALL match jqdatasdk format

### Requirement: wealthdata get_fundamentals API
The `wealthdata` module SHALL provide `get_fundamentals()` function compatible with jqdatasdk.

The function SHALL:
- Accept `valuation` query object (may be simplified for crypto)
- Accept optional `statDate` and `statDateCount` parameters (ignored)
- Return pandas DataFrame with basic trading pair information OR empty DataFrame
- Issue warning that financial data concept doesn't fully apply to cryptocurrency
- Return available data (market cap, 24h volume, etc.) if possible

#### Scenario: Get fundamentals for trading pair
- **WHEN** a strategy calls `wealthdata.get_fundamentals(valuation, ...)`
- **THEN** the function SHALL return a DataFrame with available trading pair information
- **OR** return empty DataFrame with warning if financial data is not applicable
- **AND** the function SHALL issue a UserWarning explaining the limitation

### Requirement: wealthdata get_industry API
The `wealthdata` module SHALL provide `get_industry()` function compatible with jqdatasdk.

The function SHALL:
- Accept `security` parameter (trading pair symbol)
- Accept optional `date` parameter (ignored, returns current category)
- Return string representing the industry/category (e.g., 'Layer1', 'DeFi', 'Layer2')
- Get category mapping from configuration or Context
- Return empty string or 'Unknown' if category not found

#### Scenario: Get industry for trading pair
- **WHEN** a strategy calls `wealthdata.get_industry('BTCUSDT')`
- **THEN** the function SHALL return a category string (e.g., 'Layer1')
- **AND** the return format SHALL match jqdatasdk (string)

#### Scenario: Get industry for unknown trading pair
- **WHEN** a strategy calls `wealthdata.get_industry('UNKNOWNUSDT')`
- **THEN** the function SHALL return empty string or 'Unknown'
- **AND** MAY issue a warning that category is not found

## MODIFIED Requirements

### Requirement: wealthdata API Compatibility
The `wealthdata` module SHALL provide compatibility with jqdatasdk APIs, including but not limited to:
- `get_price()` - Get price data (already supported)
- `get_bars()` - Get bar data (already supported)
- `get_all_securities()` - Get all trading pairs (NEW)
- `get_trade_days()` - Get trade days (NEW)
- `get_index_stocks()` - Get index constituents (NEW)
- `get_index_weights()` - Get index weights (NEW)
- `get_fundamentals()` - Get fundamentals data (NEW, with limitations)
- `get_industry()` - Get industry/category (NEW)

The module SHALL:
- Maintain function signature compatibility with jqdatasdk
- Maintain return format compatibility (DataFrame, list, string as appropriate)
- Provide clear documentation on adaptations and limitations
- Issue warnings when concepts don't fully apply to cryptocurrency trading

#### Scenario: Strategy uses multiple wealthdata APIs
- **WHEN** a strategy uses `get_price()`, `get_all_securities()`, and `get_index_stocks()`
- **THEN** all APIs SHALL work correctly
- **AND** return formats SHALL be compatible with jqdatasdk
- **AND** the strategy code SHALL work with minimal modifications (only import change)

