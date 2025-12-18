# Design: Extensible Exchange Support Framework

## Context

The strategy framework needs to support multiple exchanges (primarily Binance, with extensibility for OKX, Bybit, etc.). Current design uses simple string identifiers but lacks:
- Clear extension mechanism for adding new exchanges
- Standardized adapter pattern for exchange-specific differences
- Documentation on how to add new exchange support

## Goals

1. Support Binance as the primary exchange with full implementation
2. Design extensible architecture for adding new exchanges (OKX, Bybit, etc.)
3. Provide unified interface abstraction hiding exchange-specific differences
4. Define clear process for adding new exchange support

## Non-Goals

- Support for exchange-specific advanced features in the initial design
- Automatic exchange detection or switching
- Real-time exchange capability discovery

## Decisions

### Decision 1: Exchange Identifier Format

**What**: Use lowercase string identifiers for exchanges (e.g., "binance", "okx", "bybit").

**Why**:
- Simple and human-readable
- Easy to extend (just add new string)
- Backward compatible with existing "binance" usage
- No proto changes required

**Format**:
- Lowercase only
- Alphanumeric and hyphens allowed
- Must be unique and stable

**Examples**:
- `binance` - Binance exchange (primary support)
- `okx` - OKX exchange (future support)
- `bybit` - Bybit exchange (future support)

### Decision 2: Adapter Layer Pattern

**What**: Implement exchange adapter layer in Python SDK to handle exchange-specific differences.

**Why**:
- Isolates exchange-specific logic from strategy code
- Provides unified interface for all exchanges
- Makes adding new exchanges straightforward
- Allows exchange-specific optimizations

**Architecture**:
```
Strategy Code
    ↓
Python SDK (Unified Interface)
    ↓
Exchange Adapter Layer
    ├── BinanceAdapter
    ├── OKXAdapter (future)
    └── BybitAdapter (future)
    ↓
Exchange-Specific Configuration
```

### Decision 3: Binance as Primary Reference

**What**: Binance is the primary supported exchange with complete implementation as reference.

**Why**:
- Binance is the main exchange for current use cases
- Provides complete reference implementation for future exchanges
- Allows optimization for Binance-specific features
- Clear migration path for other exchanges

**Implementation**:
- Binance adapter fully implemented
- Binance configuration documented
- Binance-specific constraints clearly stated
- Other exchanges follow Binance adapter pattern

### Decision 4: Extension Process

**What**: Define standardized process for adding new exchange support.

**Steps**:
1. Create exchange adapter implementing unified interface
2. Add exchange configuration files (trading rules, commission rates)
3. Update documentation with exchange-specific notes
4. Add tests for new exchange
5. Update supported exchanges list

**Requirements**:
- Must implement all required adapter methods
- Must provide trading rules and commission rate configurations
- Must pass all adapter interface tests
- Must document exchange-specific constraints

## Risks / Trade-offs

### Risk: Exchange-Specific Features
**Mitigation**: Adapter layer isolates differences, unified interface hides complexity

### Risk: Configuration Complexity
**Mitigation**: Standardized configuration format, clear documentation

### Risk: Breaking Changes
**Mitigation**: Adapter pattern allows changes without affecting strategy code

## Migration Plan

### Phase 1: Framework Design
- Define adapter interface
- Design configuration format
- Document extension process

### Phase 2: Binance Implementation
- Implement Binance adapter
- Create Binance configuration
- Add Binance-specific documentation

### Phase 3: Extension Support
- Document extension process
- Create extension guide
- Add extension validation

### Rollback
- Adapter pattern allows easy removal of exchange support
- No breaking changes to strategy interface

## Open Questions

1. Should we support exchange-specific order types?
   - **Answer**: Initially no, use unified order types. Exchange-specific features can be added via adapter extensions.

2. How to handle exchange-specific error codes?
   - **Answer**: Adapter layer normalizes errors to standard error types.

3. Should we validate exchange identifiers?
   - **Answer**: Yes, at SDK level. Invalid exchange returns clear error.

