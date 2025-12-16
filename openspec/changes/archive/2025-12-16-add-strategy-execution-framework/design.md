# Design: Strategy Execution Framework (JoinQuant-style)

## Context

Current strategy specification defines gRPC interface (StrategySpec) but lacks a developer-friendly framework. Strategy developers need to implement gRPC services directly, which is complex. We need a framework similar to JoinQuant that allows developers to write Python strategy files with lifecycle functions.

## Goals

1. Enable developers to write Python strategy files without gRPC knowledge
2. Provide lifecycle functions (initialize, before_trading, handle_bar, etc.)
3. Automatically dispatch events to appropriate strategy functions
4. Provide unified Context object for account, market data, and order operations
5. Support backtesting, simulation, and live trading with same code

## Non-Goals

- Support for non-Python languages (Python only initially)
- Advanced strategy features (focus on core framework first)
- Real-time market data streaming (event-driven only)

## Decisions

### Decision 1: Lifecycle Function Pattern

**What**: Use lifecycle functions similar to JoinQuant:
- `initialize(context)` - Called once at strategy start
- `before_trading(context)` - Called before each trading period
- `handle_bar(context, bar)` - Called when new bar data arrives
- `on_order(context, order)` - Called when order status changes
- `on_risk_event(context, event)` - Called when risk events occur

**Why**:
- Familiar pattern for quant developers
- Clear separation of concerns
- Easy to understand and maintain
- Aligns with JoinQuant ecosystem

**Implementation**:
```python
def initialize(context):
    # Strategy initialization
    pass

def before_trading(context):
    # Pre-trading setup
    pass

def handle_bar(context, bar):
    # Process new bar data
    pass

def on_order(context, order):
    # Handle order status changes
    pass

def on_risk_event(context, event):
    # Handle risk events
    pass
```

### Decision 2: Context Object Design

**What**: Provide unified Context object with:
- Account information (balances, positions, risk metrics)
- Market data access (current bar, historical bars, indicators)
- Order operations (buy, sell, cancel)
- Trading rules and commission rates

**Why**:
- Single source of truth for strategy state
- Hides complexity of ExecRequest/ExecResponse
- Provides convenient methods for common operations
- Consistent interface across environments

**Interface** (simplified):
```python
class Context:
    account: Account
    portfolio: Portfolio
    current_bar: Bar
    history(symbol, count, timeframe): List[Bar]
    order_buy(symbol, quantity, price=None): Order
    order_sell(symbol, quantity, price=None): Order
    cancel_order(order_id): bool
```

### Decision 3: Event-to-Function Mapping

**What**: Map ExecRequest trigger types to strategy functions:
- `MARKET_DATA_TRIGGER_TYPE` → `handle_bar(context, bar)`
- `ORDER_STATUS_TRIGGER_TYPE` → `on_order(context, order)`
- `RISK_MANAGE_TRIGGER_TYPE` → `on_risk_event(context, event)`

**Why**:
- Direct mapping from system events to strategy logic
- Clear and predictable behavior
- Easy to extend for new trigger types

### Decision 4: Engine as Strategy Implementation

**What**: Engine implements StrategySpec gRPC service, wrapping Python strategies.

**Why**:
- Maintains existing gRPC interface
- Allows both framework-based and direct gRPC strategies
- Backward compatible
- Clear separation of concerns

**Architecture**:
```
Strategy Management System
    ↓ (gRPC call)
StrategySpec.Exec(ExecRequest)
    ↓
Strategy Execution Engine
    ├── Load Python strategy file
    ├── Build Context from ExecRequest
    ├── Map trigger to lifecycle function
    ├── Call strategy function
    ├── Collect order operations
    └── Return ExecResponse
```

### Decision 5: Strategy File Format

**What**: Python file with lifecycle functions, no special class or structure required.

**Why**:
- Simple and familiar
- Easy to write and test
- No boilerplate code
- Flexible and extensible

**Example**:
```python
# strategy.py
def initialize(context):
    context.symbol = "BTCUSDT"
    context.ma_period = 20

def handle_bar(context, bar):
    # Strategy logic
    ma = context.history(context.symbol, context.ma_period, "1h")
    if bar.close > ma[-1]:
        context.order_buy(context.symbol, 0.1)
```

## Risks / Trade-offs

### Risk: Performance Overhead
**Mitigation**: Engine overhead is minimal, focus on efficient Context object and event dispatch

### Risk: State Management Complexity
**Mitigation**: Context object manages state, strategy remains stateless at function level

### Risk: Error Handling
**Mitigation**: Engine catches all exceptions, returns appropriate ExecResponse with error messages

### Trade-off: Flexibility vs Simplicity
**Decision**: Prioritize simplicity, add flexibility through Context extensions if needed

## Migration Plan

### Phase 1: Framework Design
- Define lifecycle functions
- Design Context object interface
- Design event mapping rules

### Phase 2: Engine Implementation
- Implement strategy loader
- Implement event dispatcher
- Implement Context manager
- Implement lifecycle manager

### Phase 3: SDK Development
- Implement Context object
- Implement order operations
- Implement market data access
- Add helper utilities

### Phase 4: Integration
- Integrate with StrategySpec
- Add strategy management
- Add monitoring and logging

### Rollback
- Engine is optional layer, can fall back to direct gRPC implementation
- No breaking changes to existing interface

## Open Questions

1. Should we support strategy state persistence?
   - **Answer**: Initially no, keep stateless. Can add later if needed.

2. How to handle strategy errors?
   - **Answer**: Engine catches exceptions, returns FAILED status with error message.

3. Should we support multiple symbols in one strategy?
   - **Answer**: Initially single symbol, can extend later.

4. How to handle strategy parameters?
   - **Answer**: Through ExecRequest.strategy_param, accessible via context.params.

