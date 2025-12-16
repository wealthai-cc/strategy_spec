# Strategy Testing Visualization Specification

## ADDED Requirements

### Requirement: Strategy Test Visualization Frontend
The system SHALL provide a visualization frontend for strategy testing that displays K-line charts, buy/sell signals, trade details, execution timeline, and framework verification results.

#### Scenario: Generate visualization report for strategy test
- **WHEN** a user runs `python3 test_strategy.py strategy/double_mean.py --visualize`
- **THEN** the system SHALL collect test data (K-line data, order operations, function calls, framework checks)
- **AND** the system SHALL generate an HTML report containing:
  - K-line chart with buy/sell point markers
  - Trade details table
  - Strategy execution timeline
  - Framework verification panel
- **AND** the system SHALL save the report to a file
- **AND** the system SHALL display the report path to the user

### Requirement: K-line Chart Display
The visualization frontend SHALL display K-line (candlestick) charts showing OHLCV data from test execution.

#### Scenario: Display K-line chart with test data
- **WHEN** test data contains K-line bars
- **THEN** the system SHALL render a candlestick chart showing:
  - Open, High, Low, Close prices for each bar
  - Volume bars (optional)
  - Time axis with proper labels
  - Price axis with proper labels
- **AND** the chart SHALL support different market types (A股, 美股, 港股, 加密货币) with appropriate price ranges

### Requirement: Buy/Sell Point Markers
The visualization frontend SHALL mark buy and sell signals on the K-line chart.

#### Scenario: Mark buy point on chart
- **WHEN** a buy order is placed during strategy execution
- **THEN** the system SHALL mark the buy point on the K-line chart with:
  - Green upward arrow at the buy price
  - Label showing buy price and quantity
  - Timestamp of the buy order

#### Scenario: Mark sell point on chart
- **WHEN** a sell order is placed during strategy execution
- **THEN** the system SHALL mark the sell point on the K-line chart with:
  - Red downward arrow at the sell price
  - Label showing sell price and quantity
  - Timestamp of the sell order

#### Scenario: Handle overlapping markers
- **WHEN** multiple buy/sell points occur at the same K-line
- **THEN** the system SHALL adjust marker positions to avoid overlap
- **AND** the system SHALL display all markers clearly

### Requirement: Trade Details Display
The visualization frontend SHALL display detailed information for each trade point.

#### Scenario: Display trade details table
- **WHEN** orders are placed during strategy execution
- **THEN** the system SHALL display a trade details table containing:
  - Trade time (timestamp)
  - Trade price
  - Trade quantity
  - Trade direction (buy/sell)
  - Trade reason (strategy logic trigger condition, e.g., "价格 > MA5 * 1.01")
  - Order status
  - Order ID (if available)

#### Scenario: Display trade statistics
- **WHEN** trades are executed
- **THEN** the system SHALL calculate and display:
  - Total number of trades
  - Number of buy orders
  - Number of sell orders
  - Average trade price
  - Total trade amount

### Requirement: Strategy Execution Timeline
The visualization frontend SHALL display a timeline showing the sequence of strategy function calls.

#### Scenario: Display execution timeline
- **WHEN** a strategy is executed
- **THEN** the system SHALL display a timeline showing:
  - Function call sequence (initialize, before_trading, handle_bar, etc.)
  - Function call timestamps
  - Function execution results (success/failure)
  - run_daily registered function calls
  - Order operations triggered by each function

### Requirement: Framework Verification Display
The visualization frontend SHALL display framework function verification results.

#### Scenario: Display framework verification panel
- **WHEN** a strategy test completes
- **THEN** the system SHALL display a framework verification panel showing:
  - List of injected functions (g, log, run_daily, order_value, order_target, etc.)
  - Status of each function (✓ injected / ✗ not injected)
  - wealthdata API calls made during execution
  - Order operation statistics
  - Color coding (green = normal, red = abnormal)

### Requirement: HTML Report Generation
The visualization frontend SHALL generate a complete HTML report containing all visualization components.

#### Scenario: Generate HTML report
- **WHEN** visualization is enabled
- **THEN** the system SHALL generate an HTML report file containing:
  - K-line chart (embedded as base64 image or plotly interactive chart)
  - Trade details table
  - Strategy execution timeline
  - Framework verification panel
  - Proper styling (CSS)
  - Report metadata (strategy name, test time, market type)

#### Scenario: Save and open report
- **WHEN** HTML report is generated
- **THEN** the system SHALL save the report to a file (default: `strategy_report_YYYYMMDD_HHMMSS.html`)
- **AND** the system SHALL display the report path to the user
- **AND** the system SHALL optionally open the report in a browser

### Requirement: Test Tool Integration
The visualization functionality SHALL be integrated into `test_strategy.py` with backward compatibility.

#### Scenario: Enable visualization via command line
- **WHEN** a user runs `python3 test_strategy.py strategy/double_mean.py --visualize`
- **THEN** the system SHALL collect visualization data during test execution
- **AND** the system SHALL generate the HTML report after test completion
- **AND** the system SHALL not break existing functionality when visualization is disabled

#### Scenario: Specify output path
- **WHEN** a user runs `python3 test_strategy.py strategy/double_mean.py --visualize --output custom_report.html`
- **THEN** the system SHALL save the report to the specified path
- **AND** the system SHALL create the directory if it doesn't exist

### Requirement: Data Collection
The system SHALL collect all necessary data during strategy test execution for visualization.

#### Scenario: Collect K-line data
- **WHEN** test execution provides market data context
- **THEN** the system SHALL collect:
  - OHLCV data for each bar
  - Bar timestamps (open_time, close_time)
  - Symbol and timeframe information

#### Scenario: Collect order operations
- **WHEN** orders are placed during strategy execution
- **THEN** the system SHALL collect:
  - Order type (buy/sell)
  - Order price
  - Order quantity
  - Order timestamp
  - Order status
  - Trigger condition (if available from strategy logic)

#### Scenario: Collect function calls
- **WHEN** strategy functions are called during execution
- **THEN** the system SHALL collect:
  - Function name
  - Call timestamp
  - Execution result (success/failure/error message)
  - Function arguments (if relevant)

#### Scenario: Collect framework verification data
- **WHEN** strategy is loaded and executed
- **THEN** the system SHALL collect:
  - List of injected functions and their status
  - wealthdata API calls made
  - Order operation statistics
  - Framework feature checks

