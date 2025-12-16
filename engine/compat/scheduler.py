"""
Scheduled function registration for run_daily compatibility.
"""

from typing import Callable, Optional, Any, Dict, List


# Global registry for scheduled functions per strategy module
_scheduled_functions: Dict[Any, List[Dict[str, Any]]] = {}


def create_run_daily_function(strategy_module: Any) -> Callable:
    """
    Create a run_daily function for a strategy module.
    
    Args:
        strategy_module: The strategy module object
    
    Returns:
        A run_daily function bound to this strategy module
    """
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
        if strategy_module not in _scheduled_functions:
            _scheduled_functions[strategy_module] = []
        
        _scheduled_functions[strategy_module].append({
            'func': func,
            'time': time,
            'reference_security': reference_security,
        })
    
    return run_daily


def get_scheduled_functions(strategy_module: Any) -> List[Dict[str, Any]]:
    """
    Get scheduled functions for a strategy module.
    
    Args:
        strategy_module: The strategy module object
    
    Returns:
        List of scheduled function registrations
    """
    return _scheduled_functions.get(strategy_module, [])

