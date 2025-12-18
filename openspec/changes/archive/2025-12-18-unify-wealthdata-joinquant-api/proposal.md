# Change: Unify All JoinQuant APIs in wealthdata Module

## Why

Currently, JoinQuant-compatible functions are scattered across multiple modules and require runtime injection. This creates several issues:

1. **Inconsistent access patterns**: Some functions are injected into strategy modules, while others are in `wealthdata`. Strategies must use `from wealthdata import *` but some functions may not be available or may not work correctly.

2. **Debug visibility issues**: When strategies add debug logging (e.g., `log.debug()`), the output is not visible because log objects may not be properly initialized or their output streams are not configured correctly.

3. **Maintenance complexity**: Having functions in multiple places (`engine/compat/`, `wealthdata.py`, and runtime injection) makes it harder to maintain and ensure all JoinQuant APIs are available.

4. **User confusion**: Users expect all JoinQuant-compatible APIs to be available through `from wealthdata import *`, but the current implementation doesn't guarantee this.

## What Changes

- **MODIFIED**: All JoinQuant-compatible functions, classes, and objects SHALL be defined in the `wealthdata` module
- **MODIFIED**: Strategies SHALL be able to use `from wealthdata import *` to access all JoinQuant APIs without any runtime injection
- **MODIFIED**: Log output SHALL be visible and properly configured for debugging
- **REMOVED**: Runtime injection of functions into strategy modules (all functions come from `wealthdata` only)
- **MODIFIED**: Strategy loader SHALL only set up strategy-specific instances (g, log) in `wealthdata` module, not inject into strategy modules

## Impact

- **Affected specs**: 
  - `strategy-development` - How strategies access JoinQuant APIs
  - `strategy-engine` - How the engine sets up strategy execution environment
- **Affected code**:
  - `wealthdata.py` - Main module that provides all APIs
  - `engine/loader/loader.py` - Strategy loading and setup
  - `engine/compat/*.py` - Compatibility modules (may be refactored or removed)
- **Breaking changes**: 
  - **BREAKING**: Strategies that rely on direct module injection (without `from wealthdata import *`) will need to be updated
  - Strategies must use `from wealthdata import *` to access all JoinQuant APIs

