"""
Event dispatcher for mapping ExecRequest triggers to strategy functions.
"""

from typing import Dict, Optional, Callable, Any, Tuple
from enum import IntEnum


class TriggerType(IntEnum):
    """Trigger type enum matching proto definition."""
    INVALID_TRIGGER_TYPE = 0
    MARKET_DATA_TRIGGER_TYPE = 1
    RISK_MANAGE_TRIGGER_TYPE = 2
    ORDER_STATUS_TRIGGER_TYPE = 3


class EventDispatcher:
    """
    Maps ExecRequest trigger types to strategy lifecycle functions.
    """
    
    # Mapping from trigger type to function name
    TRIGGER_TO_FUNCTION = {
        TriggerType.MARKET_DATA_TRIGGER_TYPE: "handle_bar",
        TriggerType.ORDER_STATUS_TRIGGER_TYPE: "on_order",
        TriggerType.RISK_MANAGE_TRIGGER_TYPE: "on_risk_event",
    }
    
    def __init__(self, strategy_functions: Dict[str, Optional[Callable]]):
        """
        Initialize event dispatcher.
        
        Args:
            strategy_functions: Dictionary of strategy lifecycle functions
        """
        self.strategy_functions = strategy_functions
    
    def dispatch(
        self,
        trigger_type: int,
        trigger_detail: Dict[str, Any],
        context: Any,
        market_data_context: list,
        incomplete_orders: list,
    ) -> Tuple[Optional[str], Optional[Callable], Optional[Any]]:
        """
        Dispatch trigger event to appropriate strategy function.
        
        Args:
            trigger_type: Trigger type from ExecRequest
            trigger_detail: Trigger detail from ExecRequest
            context: Context object
            market_data_context: Market data context
            incomplete_orders: List of incomplete orders
        
        Returns:
            Tuple of (function_name, function_callable, function_args)
            Returns (None, None, None) if no matching function
        """
        trigger = TriggerType(trigger_type)
        
        if trigger == TriggerType.INVALID_TRIGGER_TYPE:
            return None, None, None
        
        # Get function name from mapping
        function_name = self.TRIGGER_TO_FUNCTION.get(trigger)
        if function_name is None:
            return None, None, None
        
        # Get function from strategy
        func = self.strategy_functions.get(function_name)
        if func is None:
            # Function not implemented in strategy, skip
            return function_name, None, None
        
        # Prepare function arguments based on trigger type
        if trigger == TriggerType.MARKET_DATA_TRIGGER_TYPE:
            # handle_bar(context, bar)
            if not market_data_context or not market_data_context[0].get("bars"):
                return function_name, None, None
            
            # Get latest bar
            latest_bar_data = market_data_context[0]["bars"][-1]
            from ..context.context import Bar
            bar = Bar(
                open_time=latest_bar_data.get("open_time", 0),
                close_time=latest_bar_data.get("close_time", 0),
                open=latest_bar_data.get("open", "0"),
                high=latest_bar_data.get("high", "0"),
                low=latest_bar_data.get("low", "0"),
                close=latest_bar_data.get("close", "0"),
                volume=latest_bar_data.get("volume", "0"),
            )
            return function_name, func, (context, bar)
        
        elif trigger == TriggerType.ORDER_STATUS_TRIGGER_TYPE:
            # on_order(context, order)
            # Get the order that triggered this event
            # For now, we'll use the first incomplete order or create from detail
            # In real implementation, trigger_detail should contain order info
            if incomplete_orders and len(incomplete_orders) > 0:
                # incomplete_orders is already a list of Order objects
                order = incomplete_orders[0]
            else:
                # Create order from trigger detail if available
                from ..context.context import Order
                order = Order()
            return function_name, func, (context, order)
        
        elif trigger == TriggerType.RISK_MANAGE_TRIGGER_TYPE:
            # on_risk_event(context, event)
            from ..context.context import RiskEvent
            risk_event = RiskEvent(
                risk_event_type=trigger_detail.get("risk_event_type", 0),
                remark=trigger_detail.get("remark", ""),
            )
            return function_name, func, (context, risk_event)
        
        return None, None, None

