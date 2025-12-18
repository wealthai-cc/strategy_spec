## 1. Analysis and Design
- [x] 1.1 Audit all JoinQuant-compatible functions and identify their current locations
- [x] 1.2 Document which functions are currently injected vs. defined in wealthdata
- [x] 1.3 Identify log output visibility issues and root causes
- [x] 1.4 Design unified wealthdata module structure

## 2. Refactor wealthdata Module
- [x] 2.1 Ensure all JoinQuant functions are defined in `wealthdata.py`:
  - [x] Data access: `get_price`, `get_bars`, `get_all_securities`, `get_trade_days`, `get_index_stocks`, `get_index_weights`, `get_fundamentals`, `get_industry`, `get_trades`
  - [x] Strategy functions: `log`, `g`, `run_daily`, `order_value`, `order_target`
  - [x] Configuration: `set_benchmark`, `set_option`, `set_order_cost`, `OrderCost`
- [x] 2.2 Update `__all__` list to include all exported functions
- [x] 2.3 Ensure all functions work correctly when imported via `from wealthdata import *`

## 3. Fix Log Output Visibility
- [x] 3.1 Ensure log objects are properly initialized with correct output streams
- [x] 3.2 Fix log object references in strategy modules after `from wealthdata import *`
- [x] 3.3 Test that `log.info()`, `log.debug()`, `log.warn()`, `log.error()` all produce visible output
- [x] 3.4 Ensure log output appears in test execution output

## 4. Update Strategy Loader
- [x] 4.1 Remove all module injection code from `engine/loader/loader.py`
- [x] 4.2 Update loader to only set up strategy-specific instances in `wealthdata` module:
  - [x] Create strategy-specific `g` object in `wealthdata.g`
  - [x] Create strategy-specific `log` object in `wealthdata.log`
  - [x] Set strategy module in thread-local storage for `run_daily`, `set_benchmark`, etc.
- [x] 4.3 Ensure strategy module references are updated after import

## 5. Testing and Validation
- [x] 5.1 Test `double_mean.py` strategy with `from wealthdata import *`
- [x] 5.2 Verify all log outputs are visible (info, debug, warn, error)
- [x] 5.3 Verify all JoinQuant APIs work correctly:
  - [x] Data access functions
  - [x] Order functions
  - [x] Configuration functions
  - [x] Scheduled functions (run_daily)
- [x] 5.4 Test with multiple strategies to ensure isolation
- [x] 5.5 Update existing tests to reflect new architecture

## 6. Documentation
- [x] 6.1 Update strategy development guide to emphasize `from wealthdata import *`
- [x] 6.2 Document that all JoinQuant APIs are available through wealthdata
- [x] 6.3 Update migration guide if needed
- [x] 6.4 Add examples showing proper usage

