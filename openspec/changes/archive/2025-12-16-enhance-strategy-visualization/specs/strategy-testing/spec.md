# Strategy Testing Visualization Enhancement Specification

## MODIFIED Requirements

### Requirement: Test Tool Integration
The visualization functionality SHALL be automatically enabled for every strategy test execution, without requiring explicit parameters.

#### Scenario: Automatic visualization generation
- **WHEN** a user runs `python3 test_strategy.py strategy/double_mean.py`
- **THEN** the system SHALL automatically collect visualization data during test execution
- **AND** the system SHALL automatically generate an HTML report after test completion
- **AND** the system SHALL save the report to a file with default naming (`{strategy_name}_report.html`)
- **AND** the system SHALL display the report path to the user

#### Scenario: Custom output path
- **WHEN** a user runs `python3 test_strategy.py strategy/double_mean.py --output custom_report.html`
- **THEN** the system SHALL save the report to the specified path
- **AND** the system SHALL create the directory if it doesn't exist

### Requirement: Timeframe Auto-Detection
The system SHALL automatically detect the timeframe used by the strategy and generate test data with matching granularity.

#### Scenario: Detect timeframe from strategy code
- **WHEN** a strategy uses `get_bars(symbol, count=5, unit='1h')` or `get_bars(symbol, count=5, frequency='1h')`
- **THEN** the system SHALL detect the timeframe as '1h'
- **AND** the system SHALL generate test data with 1-hour granularity
- **AND** the system SHALL generate sufficient bars to match the strategy's data requirements

#### Scenario: Default timeframe when detection fails
- **WHEN** the system cannot detect the timeframe from strategy code
- **THEN** the system SHALL use '1d' (daily) as the default timeframe
- **AND** the system SHALL display a warning message to the user

#### Scenario: Generate matching granularity data
- **WHEN** a strategy uses 1-hour timeframe and requires 20 bars
- **THEN** the system SHALL generate 20 hours of 1-hour K-line data
- **AND** the data SHALL match the strategy's expected granularity

## ADDED Requirements

### Requirement: Strategy Decision Information Collection
The system SHALL collect comprehensive decision information during strategy execution, including technical indicators, trigger conditions, decision rationale, and strategy state.

#### Scenario: Collect technical indicator values
- **WHEN** a strategy calculates technical indicators (e.g., MA5, MA20)
- **THEN** the system SHALL collect the indicator values at decision points
- **AND** the system SHALL store them with timestamps for visualization

#### Scenario: Collect trigger conditions
- **WHEN** a strategy evaluates trigger conditions (e.g., "price > MA5 * 1.01")
- **THEN** the system SHALL collect the condition expression
- **AND** the system SHALL collect the condition evaluation result (true/false)
- **AND** the system SHALL store them with timestamps

#### Scenario: Collect decision rationale
- **WHEN** a strategy makes a buy or sell decision
- **THEN** the system SHALL collect the decision rationale (e.g., "价格高于均价1%，买入")
- **AND** the system SHALL collect from strategy logs or code analysis
- **AND** the system SHALL store them with timestamps

#### Scenario: Collect strategy state
- **WHEN** a strategy makes a decision
- **THEN** the system SHALL collect the strategy state at that moment:
  - Available cash
  - Current positions
  - Portfolio value
  - Other relevant state information
- **AND** the system SHALL store them with timestamps

### Requirement: Enhanced Buy/Sell Point Markers
The visualization frontend SHALL display comprehensive decision information in buy/sell point markers.

#### Scenario: Display complete decision information
- **WHEN** a buy or sell order is placed
- **THEN** the marker SHALL display:
  - Price and quantity
  - Technical indicator values (e.g., MA5=10.65, MA20=10.50)
  - Trigger condition (e.g., "price > MA5 * 1.01")
  - Condition result (true/false)
  - Decision rationale (e.g., "价格高于均价1%，买入")
  - Strategy state (available cash, positions, etc.)
- **AND** the information SHALL be clearly formatted and readable

#### Scenario: Handle information overflow
- **WHEN** the decision information is too long to fit in the marker
- **THEN** the system SHALL use appropriate formatting (line breaks, scrolling, or tooltip)
- **AND** the system SHALL ensure all information is accessible

### Requirement: Technical Indicator Visualization
The visualization frontend SHALL overlay technical indicator lines on the K-line chart.

#### Scenario: Display MA lines
- **WHEN** a strategy uses MA5 or MA20 indicators
- **THEN** the system SHALL calculate and display the MA lines on the chart
- **AND** the lines SHALL be clearly labeled (MA5, MA20)
- **AND** the lines SHALL use different colors for distinction
- **AND** the chart SHALL include a legend explaining the lines

#### Scenario: Display other indicators
- **WHEN** a strategy uses other technical indicators (EMA, RSI, etc.)
- **THEN** the system SHALL display them on the chart if applicable
- **AND** the system SHALL use appropriate visualization methods (lines, histograms, etc.)

### Requirement: Chart Attribution
The visualization frontend SHALL provide clear attribution for strategy decisions, showing why decisions were made.

#### Scenario: Display trigger condition thresholds
- **WHEN** a strategy uses threshold-based trigger conditions
- **THEN** the system SHALL display threshold lines on the chart
- **AND** the lines SHALL be labeled with the condition (e.g., "MA5 * 1.01")
- **AND** the system SHALL indicate when conditions are met or not met

#### Scenario: Annotate key decision points
- **WHEN** a strategy makes a decision
- **THEN** the system SHALL annotate the chart at the decision point
- **AND** the annotation SHALL include the decision type and key information
- **AND** the annotation SHALL be clearly visible and readable

#### Scenario: Provide chart legend
- **WHEN** a chart contains multiple elements (K-lines, indicators, markers)
- **THEN** the system SHALL provide a comprehensive legend
- **AND** the legend SHALL explain the meaning of each element
- **AND** the legend SHALL be clearly positioned and readable

### Requirement: Decision Information Panel
The HTML report SHALL include a dedicated panel displaying decision information.

#### Scenario: Display decision information table
- **WHEN** decisions are made during strategy execution
- **THEN** the report SHALL display a decision information table containing:
  - Decision time
  - Decision type (buy/sell)
  - Technical indicator values
  - Trigger condition and result
  - Decision rationale
  - Strategy state
- **AND** the table SHALL be sortable and filterable

#### Scenario: Display technical indicators table
- **WHEN** technical indicators are calculated
- **THEN** the report SHALL display a technical indicators table
- **AND** the table SHALL show indicator values at each time point
- **AND** the table SHALL be clearly formatted
