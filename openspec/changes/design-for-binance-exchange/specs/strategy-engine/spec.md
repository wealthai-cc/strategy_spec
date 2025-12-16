## MODIFIED Requirements

### Requirement: ExecRequest Exchange Field
The `ExecRequest.exchange` field SHALL be set to "binance" as this strategy framework is designed specifically for Binance exchange.

The exchange field value SHALL always be "binance" and SHALL NOT support other exchange identifiers. This design decision simplifies the framework and allows optimization for Binance-specific features and constraints.

#### Scenario: Strategy execution with Binance exchange
- **WHEN** a strategy execution request is made
- **THEN** the `exchange` field SHALL be set to "binance"
- **AND** the system SHALL use Binance API endpoints and configurations
- **AND** the Python SDK SHALL query Binance-specific trading rules and commission rates

#### Scenario: Invalid exchange identifier
- **WHEN** an execution request contains an exchange value other than "binance"
- **THEN** the system SHALL return an error or warning
- **AND** the strategy execution MAY be rejected

