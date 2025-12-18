"""
wealthdata - JoinQuant jqdata compatibility layer

This is a top-level module that provides all JoinQuant-compatible APIs.
All functions, classes, and objects are defined here, allowing strategies to use:

    from wealthdata import *

This includes:
- Data access functions (get_price, get_bars, etc.)
- Strategy functions (log, g, run_daily, order_value, order_target)
- Configuration functions (set_benchmark, set_option, set_order_cost, OrderCost)
"""

# Import all public APIs from engine.wealthdata
from engine.wealthdata import (
    get_price,
    get_bars,
    get_all_securities,
    get_trade_days,
    get_index_stocks,
    get_index_weights,
    get_fundamentals,
    get_industry,
    get_trades,
    set_context,
    get_context,
    clear_context,
    bars_to_dataframe,
)

# Import compatibility modules
from types import SimpleNamespace
import sys
from typing import Optional, Dict, Callable, Any
import threading

# Thread-local storage for strategy module context
_strategy_module_local = threading.local()


def _get_strategy_module() -> Optional[Any]:
    """Get current strategy module from thread-local storage."""
    return getattr(_strategy_module_local, 'module', None)


def _set_strategy_module(module: Any) -> None:
    """Set current strategy module to thread-local storage."""
    _strategy_module_local.module = module


def _clear_strategy_module() -> None:
    """Clear current strategy module from thread-local storage."""
    if hasattr(_strategy_module_local, 'module'):
        delattr(_strategy_module_local, 'module')


# ============================================================================
# Logging module (log)
# ============================================================================

class Log:
    """Simple logging class compatible with JoinQuant's log interface."""
    
    def __init__(self, output_stream=None):
        self.output_stream = output_stream or sys.stdout
        self._log_levels = {}
    
    def info(self, message: str) -> None:
        self._log('INFO', message)
    
    def warn(self, message: str) -> None:
        self._log('WARN', message)
    
    def error(self, message: str) -> None:
        self._log('ERROR', message)
    
    def debug(self, message: str) -> None:
        self._log('DEBUG', message)
    
    def set_level(self, category: str, level: str) -> None:
        self._log_levels[category] = level
    
    def _log(self, level: str, message: str) -> None:
        log_line = f"[{level}] {message}\n"
        self.output_stream.write(log_line)
        self.output_stream.flush()


# Create a default log instance (will be replaced per strategy)
log = Log()


# ============================================================================
# Global variable object (g)
# ============================================================================

# Create a default g object (will be replaced per strategy)
g = SimpleNamespace()


# ============================================================================
# Order functions (order_value, order_target)
# ============================================================================

from engine.compat.market_type import detect_market_type, MarketType


def order_value(symbol: str, value: float, price: Optional[float] = None) -> Any:
    """
    Place an order for a specified value amount.
    
    Args:
        symbol: Trading symbol
        value: Order value amount
        price: Optional limit price (None for market order)
    
    Returns:
        Order object
    """
    context = get_context()
    if context is None:
        raise RuntimeError("No context available. order_value() must be called during strategy execution.")
    
    if price is None:
        if context.current_bar is None:
            raise ValueError("Cannot determine price: current_bar is None")
        price = float(context.current_bar.close)
    
    # Calculate quantity
    quantity = value / price
    
    # Adjust quantity based on market type
    market_type = detect_market_type(symbol, context)
    if market_type in [MarketType.A_STOCK, MarketType.US_STOCK, MarketType.HK_STOCK]:
        # Stock market: round to integer (whole shares)
        quantity = int(quantity)
    
    # Check if quantity is valid (must be > 0)
    if quantity <= 0:
        raise ValueError(f"Cannot place order: calculated quantity ({quantity}) is zero or negative. "
                       f"Value: {value}, Price: {price}")
    
    # Place buy order
    return context.order_buy(symbol, quantity, price)


def _get_position_qty(context: Any, symbol: str) -> float:
    """Get current position quantity for a symbol."""
    if hasattr(context, 'portfolio') and hasattr(context.portfolio, 'positions'):
        positions = context.portfolio.positions
        if isinstance(positions, dict):
            if symbol in positions:
                pos = positions[symbol]
                if isinstance(pos, dict):
                    return float(pos.get('quantity', 0))
                return float(getattr(pos, 'quantity', 0))
        elif isinstance(positions, list):
            for pos in positions:
                pos_symbol = pos.get('symbol', '') if isinstance(pos, dict) else getattr(pos, 'symbol', '')
                if pos_symbol == symbol:
                    qty = pos.get('quantity', 0) if isinstance(pos, dict) else getattr(pos, 'quantity', 0)
                    return float(qty)
    
    if hasattr(context, 'account') and hasattr(context.account, 'positions'):
        for pos in context.account.positions:
            pos_symbol = pos.get('symbol', '') if isinstance(pos, dict) else getattr(pos, 'symbol', '')
            if pos_symbol == symbol:
                qty = pos.get('quantity', 0) if isinstance(pos, dict) else getattr(pos, 'quantity', 0)
                return float(qty)
    
    return 0.0


def order_target(symbol: str, target_qty: float, price: Optional[float] = None) -> Optional[Any]:
    """
    Adjust position to target quantity.
    
    Args:
        symbol: Trading symbol
        target_qty: Target position quantity
        price: Optional limit price (None for market order)
    
    Returns:
        Order object if order placed, None if already at target
    """
    context = get_context()
    if context is None:
        raise RuntimeError("No context available. order_target() must be called during strategy execution.")
    
    # Get current position quantity
    current_qty = _get_position_qty(context, symbol)
    
    # Calculate difference
    diff = target_qty - current_qty
    
    # Adjust based on market type
    market_type = detect_market_type(symbol, context)
    if market_type in [MarketType.A_STOCK, MarketType.US_STOCK, MarketType.HK_STOCK]:
        # Stock market: round to integer
        diff = int(diff)
    
    # Place order if needed
    if abs(diff) < 1e-8:  # Already at target
        return None
    elif diff > 0:
        return context.order_buy(symbol, diff, price)
    else:
        sell_qty = abs(diff)
        return context.order_sell(symbol, sell_qty, price)


# ============================================================================
# Scheduled function registration (run_daily)
# ============================================================================

# Global registry for scheduled functions per strategy module
_scheduled_functions: Dict[Any, list] = {}


def run_daily(
    func: Callable,
    time: str = 'open',
    reference_security: Optional[str] = None
) -> None:
    """
    Register a function to run at specific times.
    
    Args:
        func: Function to call
        time: Time point ('before_open', 'open', 'after_close')
        reference_security: Reference security for market type detection
    """
    strategy_module = _get_strategy_module()
    if strategy_module is None:
        raise RuntimeError("No strategy module available. run_daily() must be called during strategy initialization.")
    
    if strategy_module not in _scheduled_functions:
        _scheduled_functions[strategy_module] = []
    
    _scheduled_functions[strategy_module].append({
        'func': func,
        'time': time,
        'reference_security': reference_security,
    })


def get_scheduled_functions(strategy_module: Any) -> list:
    """Get scheduled functions for a strategy module."""
    return _scheduled_functions.get(strategy_module, [])


# ============================================================================
# Configuration functions (set_benchmark, set_option, set_order_cost)
# ============================================================================

# Global registry for strategy configuration per strategy module
_strategy_configs: Dict[Any, Dict[str, Any]] = {}


def set_benchmark(security: str) -> None:
    """Set benchmark security."""
    strategy_module = _get_strategy_module()
    if strategy_module is None:
        raise RuntimeError("No strategy module available. set_benchmark() must be called during strategy initialization.")
    
    if strategy_module not in _strategy_configs:
        _strategy_configs[strategy_module] = {
            'benchmark': None,
            'options': {},
            'order_costs': {},
        }
    
    _strategy_configs[strategy_module]['benchmark'] = security


def set_option(key: str, value: Any) -> None:
    """Set option."""
    strategy_module = _get_strategy_module()
    if strategy_module is None:
        raise RuntimeError("No strategy module available. set_option() must be called during strategy initialization.")
    
    if strategy_module not in _strategy_configs:
        _strategy_configs[strategy_module] = {
            'benchmark': None,
            'options': {},
            'order_costs': {},
        }
    
    _strategy_configs[strategy_module]['options'][key] = value


def set_order_cost(
    cost: Any,
    type: str = 'stock'  # noqa: A002
) -> None:
    """Set order cost."""
    strategy_module = _get_strategy_module()
    if strategy_module is None:
        raise RuntimeError("No strategy module available. set_order_cost() must be called during strategy initialization.")
    
    if strategy_module not in _strategy_configs:
        _strategy_configs[strategy_module] = {
            'benchmark': None,
            'options': {},
            'order_costs': {},
        }
    
    _strategy_configs[strategy_module]['order_costs'][type] = cost


# ============================================================================
# OrderCost class
# ============================================================================

class OrderCost:
    """Order cost configuration (JoinQuant compatibility)."""
    
    def __init__(
        self,
        close_tax: float = 0,
        open_commission: float = 0,
        close_commission: float = 0,
        min_commission: float = 0
    ):
        self.close_tax = close_tax
        self.open_commission = open_commission
        self.close_commission = close_commission
        self.min_commission = min_commission


# ============================================================================
# Module exports
# ============================================================================

__all__ = [
    # Data access functions
    'get_price',
    'get_bars',
    'get_all_securities',
    'get_trade_days',
    'get_index_stocks',
    'get_index_weights',
    'get_fundamentals',
    'get_industry',
    'get_trades',
    'set_context',
    'get_context',
    'clear_context',
    'bars_to_dataframe',
    # Strategy functions
    'log',
    'g',
    'run_daily',
    'order_value',
    'order_target',
    # Configuration functions
    'set_benchmark',
    'set_option',
    'set_order_cost',
    'OrderCost',
    # Internal functions (for engine use)
    '_set_strategy_module',
    '_clear_strategy_module',
    'get_scheduled_functions',
]
