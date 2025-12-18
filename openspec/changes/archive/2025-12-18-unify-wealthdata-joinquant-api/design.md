# Design: Unify All JoinQuant APIs in wealthdata Module

## Context

The current implementation has JoinQuant-compatible functions scattered across:
- `wealthdata.py` - Some data access functions
- `engine/compat/` - Order functions, config functions, log, g, scheduler
- Runtime injection - Functions injected into strategy modules during loading

This creates confusion and maintenance issues. Users expect all JoinQuant APIs to be available through `from wealthdata import *`, but the current implementation doesn't guarantee this.

Additionally, log output visibility issues occur because:
1. Log objects may be created before strategy-specific setup
2. Log references in strategy modules may not be updated after `from wealthdata import *`
3. Output streams may not be properly configured

## Goals

1. **Single source of truth**: All JoinQuant-compatible APIs defined in `wealthdata.py`
2. **Simple import**: Strategies use `from wealthdata import *` to access everything
3. **Visible debugging**: All log outputs (info, debug, warn, error) are visible
4. **Strategy isolation**: Each strategy gets its own `g` and `log` instances
5. **No runtime injection**: Remove all module injection, rely only on `wealthdata` module

## Non-Goals

- Changing the JoinQuant API signatures (maintain compatibility)
- Removing support for existing strategies (migration path provided)
- Changing the underlying execution engine architecture

## Decisions

### Decision 1: All APIs in wealthdata.py

**What**: Move all JoinQuant-compatible functions, classes, and objects to `wealthdata.py`

**Why**: 
- Single source of truth
- Easier to maintain and discover
- Matches user expectations (`from wealthdata import *`)

**Alternatives considered**:
- Keep current structure with injection: Rejected - too complex, hard to maintain
- Create separate compatibility module: Rejected - adds another layer, doesn't solve the problem

### Decision 2: Strategy-Specific Instances in wealthdata Module

**What**: Create strategy-specific `g` and `log` instances in `wealthdata` module before strategy loads

**Why**:
- Ensures `from wealthdata import *` gets the correct instances
- Maintains strategy isolation
- No need for module injection

**Implementation**:
```python
# In loader, before strategy loads:
import wealthdata
wealthdata.g = SimpleNamespace()
wealthdata.log = create_log_object()

# Strategy loads and executes:
from wealthdata import *  # Gets the correct g and log
```

### Decision 3: Update Strategy Module References After Import

**What**: After strategy loads, update any references to ensure they point to wealthdata instances

**Why**:
- Python's `from module import *` creates references at import time
- If we set instances after import, references may be stale
- Updating references ensures consistency

**Implementation**:
```python
# After strategy module loads:
if hasattr(strategy_module, 'log'):
    strategy_module.log = wealthdata.log
if hasattr(strategy_module, 'g'):
    strategy_module.g = wealthdata.g
```

### Decision 4: Log Output Stream Configuration

**What**: Ensure log objects use `sys.stdout` by default and are properly flushed

**Why**:
- `sys.stdout` is the standard output stream
- Flushing ensures output appears immediately
- No need for complex output redirection

**Implementation**:
```python
class Log:
    def __init__(self, output_stream=None):
        self.output_stream = output_stream or sys.stdout
    
    def _log(self, level: str, message: str) -> None:
        log_line = f"[{level}] {message}\n"
        self.output_stream.write(log_line)
        self.output_stream.flush()  # Ensure immediate output
```

## Risks / Trade-offs

### Risk 1: Breaking Existing Strategies

**Risk**: Strategies that don't use `from wealthdata import *` may break

**Mitigation**: 
- Update loader to ensure references are updated
- Provide migration guide
- Test with existing strategies

### Risk 2: Import Order Dependencies

**Risk**: If strategy imports wealthdata before loader sets up instances, wrong instances may be used

**Mitigation**:
- Set up instances BEFORE strategy loads
- Update references AFTER strategy loads
- Document the correct usage pattern

### Risk 3: Thread Safety

**Risk**: Multiple strategies executing concurrently may interfere with each other

**Mitigation**:
- Use thread-local storage for strategy module context
- Each strategy execution gets its own `g` and `log` instances
- Test with concurrent executions

## Migration Plan

1. **Phase 1**: Ensure all functions are in `wealthdata.py` (no breaking changes)
2. **Phase 2**: Update loader to set up instances before strategy loads
3. **Phase 3**: Remove module injection code
4. **Phase 4**: Update tests and documentation
5. **Phase 5**: Validate with existing strategies

## Open Questions

- Should we deprecate direct module access (without `from wealthdata import *`)?
- Do we need to support both patterns during transition period?
- How to handle strategies that import wealthdata in unusual ways?

