"""
Lifecycle manager for strategy execution.
"""

from typing import Dict, Optional, Callable, Any


class LifecycleManager:
    """
    Manages strategy lifecycle function calls.
    """
    
    def __init__(self, strategy_functions: Dict[str, Optional[Callable]]):
        """
        Initialize lifecycle manager.
        
        Args:
            strategy_functions: Dictionary of strategy lifecycle functions
        """
        self.strategy_functions = strategy_functions
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
        Call before_trading function if available.
        
        Args:
            context: Context object
        """
        before_trading_func = self.strategy_functions.get("before_trading")
        if before_trading_func is not None:
            before_trading_func(context)
    
    def should_call_before_trading(self) -> bool:
        """
        Check if before_trading should be called.
        
        Returns:
            True if before_trading function exists
        """
        return self.strategy_functions.get("before_trading") is not None

