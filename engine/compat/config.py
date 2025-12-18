"""
Configuration functions for JoinQuant compatibility (set_benchmark, set_option, set_order_cost).
"""

from typing import Any, Dict, Callable, Optional


def create_config_functions(strategy_module: Any) -> Dict[str, Callable]:
    """
    Create config functions for strategy use.
    
    Args:
        strategy_module: The strategy module object
    
    Returns:
        Dictionary with config functions
    """
    # Store config in module-level storage
    if not hasattr(strategy_module, '_jq_config'):
        strategy_module._jq_config = {
            'benchmark': None,
            'options': {},
            'order_costs': {},
        }
    
    def set_benchmark(security: str) -> None:
        """
        Set benchmark security (simplified: only stores, doesn't affect execution).
        
        Args:
            security: Benchmark security symbol
        """
        strategy_module._jq_config['benchmark'] = security
    
    def set_option(key: str, value: Any) -> None:
        """
        Set option (simplified: only stores, doesn't affect execution).
        
        Args:
            key: Option key
            value: Option value
        """
        strategy_module._jq_config['options'][key] = value
    
    def set_order_cost(
        cost: Any,
        type: str = 'stock'  # noqa: A002
    ) -> None:
        """
        Set order cost (simplified: only stores, doesn't affect execution).
        
        Args:
            cost: Order cost object (simplified: accepts any object)
            type: Security type ('stock', 'fund', etc.)
        """
        strategy_module._jq_config['order_costs'][type] = cost
    
    return {
        'set_benchmark': set_benchmark,
        'set_option': set_option,
        'set_order_cost': set_order_cost,
    }



