"""
Lifecycle manager for strategy execution.
"""

from typing import Dict, Optional, Callable, Any
from datetime import datetime


class LifecycleManager:
    """
    Manages strategy lifecycle function calls.
    """
    
    def __init__(
        self,
        strategy_functions: Dict[str, Optional[Callable]],
        strategy_module: Optional[Any] = None
    ):
        """
        Initialize lifecycle manager.
        
        Args:
            strategy_functions: Dictionary of strategy lifecycle functions
            strategy_module: Optional strategy module object (for accessing scheduled functions)
        """
        self.strategy_functions = strategy_functions
        self.strategy_module = strategy_module
        self._initialized_contexts = set()  # Track initialized contexts by id
    
    def initialize(self, context: Any) -> None:
        """
        Call initialize function for this context if not already called.
        
        Note: Each context object should be initialized once, but different
        context objects (from different executions) should each be initialized.
        
        Args:
            context: Context object
        """
        # Use context's exec_id to track initialization per execution
        context_id = getattr(context, 'exec_id', id(context))
        if context_id in self._initialized_contexts:
            return
        
        init_func = self.strategy_functions.get("initialize")
        if init_func is not None:
            init_func(context)
            self._initialized_contexts.add(context_id)
    
    def before_trading(self, context: Any) -> None:
        """
        Call before_trading function and scheduled functions if available.
        
        This method:
        1. Calls registered scheduled functions (run_daily) that match current time
        2. Calls strategy's before_trading function if it exists
        
        Args:
            context: Context object
        """
        # Call scheduled functions first (run_daily)
        self._call_scheduled_functions(context)
        
        # Then call strategy's before_trading function
        before_trading_func = self.strategy_functions.get("before_trading")
        if before_trading_func is not None:
            before_trading_func(context)
    
    def _call_scheduled_functions(self, context: Any) -> None:
        """
        Call scheduled functions (run_daily) that match current time.
        
        Args:
            context: Context object
        """
        if self.strategy_module is None:
            return
        
        import wealthdata
        from engine.compat.market_type import detect_market_type, MarketType
        from engine.compat.market_time import is_time_match
        from engine.compat.trade_calendar import get_calendar
        
        scheduled_funcs = wealthdata.get_scheduled_functions(self.strategy_module)
        if not scheduled_funcs:
            return
        
        # Get current time (UTC)
        current_time = datetime.utcnow()
        if context.current_dt is not None:
            # Use context's current time if available
            current_time = context.current_dt
        
        # Call each scheduled function if time matches
        for scheduled in scheduled_funcs:
            func = scheduled.get('func')
            time_point = scheduled.get('time', 'open')
            reference_security = scheduled.get('reference_security')
            
            if func is None:
                continue
            
            # Detect market type from reference security or context
            market_type = MarketType.CRYPTO  # Default
            if reference_security:
                market_type = detect_market_type(reference_security, context)
            elif hasattr(context, 'current_bar') and context.current_bar:
                # Try to get symbol from market_data_context
                if hasattr(context, '_market_data_context') and context._market_data_context:
                    first_context = context._market_data_context[0]
                    symbol = first_context.get('symbol', '')
                    if symbol:
                        market_type = detect_market_type(symbol, context)
            
            # Check if it's a trading day (for stock markets)
            if market_type != MarketType.CRYPTO:
                calendar = get_calendar()
                if not calendar.is_trade_day(current_time, market_type.value):
                    # Skip if not a trading day
                    continue
            
            # Check if time matches
            if is_time_match(current_time, market_type, time_point, tolerance_minutes=30):
                try:
                    func(context)
                except Exception as e:
                    # Log error but don't stop execution
                    import sys
                    print(f"[ERROR] Scheduled function failed: {e}", file=sys.stderr)
    
    def should_call_before_trading(self) -> bool:
        """
        Check if before_trading should be called.
        
        Returns:
            True if before_trading function exists
        """
        return self.strategy_functions.get("before_trading") is not None

