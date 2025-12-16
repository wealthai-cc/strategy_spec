"""
Strategy execution engine.

Main engine that coordinates strategy loading, event dispatching, and lifecycle management.
"""

from typing import Dict, Any, Optional, List
import traceback

from .loader import StrategyLoader
from .dispatcher import EventDispatcher
from .lifecycle import LifecycleManager
from .context import Context, Account, Order, Bar


class StrategyExecutionEngine:
    """
    Strategy execution engine that wraps Python strategies.
    
    Coordinates:
    - Strategy loading
    - Event dispatching
    - Lifecycle management
    - Context object management
    """
    
    def __init__(self, strategy_path: str):
        """
        Initialize execution engine.
        
        Args:
            strategy_path: Path to Python strategy file
        """
        self.strategy_path = strategy_path
        self.loader: Optional[StrategyLoader] = None
        self.dispatcher: Optional[EventDispatcher] = None
        self.lifecycle: Optional[LifecycleManager] = None
        self._loaded = False
    
    def load_strategy(self) -> None:
        """Load strategy file and initialize components."""
        if self._loaded:
            return
        
        # Load strategy
        self.loader = StrategyLoader(self.strategy_path)
        strategy_functions = self.loader.load()
        
        # Initialize dispatcher and lifecycle manager
        self.dispatcher = EventDispatcher(strategy_functions)
        self.lifecycle = LifecycleManager(strategy_functions)
        
        self._loaded = True
    
    def execute(
        self,
        exec_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute strategy based on ExecRequest.
        
        Args:
            exec_request: ExecRequest dictionary with:
                - trigger_type: Trigger type
                - trigger_detail: Trigger detail
                - market_data_context: Market data contexts
                - account: Account information
                - incomplete_orders: Incomplete orders
                - completed_orders: Completed orders
                - exchange: Exchange name
                - exec_id: Execution ID
                - strategy_param: Strategy parameters
        
        Returns:
            ExecResponse dictionary with:
                - order_op_event: List of order operations
                - status: Execution status (0=SUCCESS, 1=PARTIAL_SUCCESS, 2=FAILED)
                - error_message: Error message if failed
                - warnings: List of warnings
        """
        try:
            # Ensure strategy is loaded
            if not self._loaded:
                self.load_strategy()
            
            # Build Context object
            context = self._build_context(exec_request)
            
            # Set context to thread-local storage for wealthdata module access
            from .wealthdata import set_context, clear_context
            set_context(context)
            
            try:
                # Initialize strategy if not already done
                # This ensures context has strategy-specific attributes set
                # Always call initialize first, regardless of trigger type
                self.lifecycle.initialize(context)
                
                # Call before_trading if appropriate
                # (In real implementation, this might be called based on timing)
                # For now, we'll skip it unless explicitly needed
                
                # Dispatch trigger event
                trigger_type = exec_request.get("trigger_type", 0)
                trigger_detail = exec_request.get("trigger_detail", {})
                market_data_context = exec_request.get("market_data_context", [])
                # Use incomplete_orders from context (already converted to Order objects)
                incomplete_orders = context._incomplete_orders
                
                func_name, func, func_args = self.dispatcher.dispatch(
                    trigger_type=trigger_type,
                    trigger_detail=trigger_detail,
                    context=context,
                    market_data_context=market_data_context,
                    incomplete_orders=incomplete_orders,
                )
                
                # Call strategy function if found
                if func is not None:
                    func(*func_args)
                
                # Collect order operations
                order_operations = context.get_order_operations()
                
                # Build response
                return {
                    "order_op_event": order_operations,
                    "status": 0,  # SUCCESS
                    "error_message": "",
                    "warnings": [],
                }
            
            finally:
                # Always clear context from thread-local storage
                clear_context()
        
        except Exception as e:
            # Return error response
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            
            # Ensure context is cleared even on error
            try:
                from .wealthdata import clear_context
                clear_context()
            except Exception:
                pass  # Ignore errors during cleanup
            
            return {
                "order_op_event": [],
                "status": 2,  # FAILED
                "error_message": f"{error_msg}\n{traceback_str}",
                "warnings": [],
            }
    
    def _build_context(self, exec_request: Dict[str, Any]) -> Context:
        """Build Context object from ExecRequest."""
        # Parse account
        account_data = exec_request.get("account", {})
        account = Account(
            account_id=account_data.get("account_id", ""),
            account_type=account_data.get("account_type", 0),
            total_net_value=account_data.get("total_net_value"),
            available_margin=account_data.get("available_margin"),
            margin_ratio=account_data.get("margin_ratio", 0.0),
            risk_level=account_data.get("risk_level", 0.0),
            leverage=account_data.get("leverage", 0.0),
            balances=account_data.get("balances", []),
            positions=account_data.get("positions", []),
        )
        
        # Parse orders
        incomplete_orders_data = exec_request.get("incomplete_orders", [])
        incomplete_orders = []
        for order_data in incomplete_orders_data:
            incomplete_orders.append(Order(
                order_id=order_data.get("order_id", ""),
                unique_id=order_data.get("unique_id", ""),
                symbol=order_data.get("symbol", ""),
                direction_type=order_data.get("direction_type", 0),
                order_type=order_data.get("order_type", 0),
                qty=order_data.get("qty", 0.0),
                limit_price=order_data.get("limit_price"),
                status=order_data.get("status", 0),
                executed_size=order_data.get("executed_size", 0.0),
                avg_fill_price=order_data.get("avg_fill_price"),
                commission=order_data.get("commission"),
                cancel_reason=order_data.get("cancel_reason"),
            ))
        
        completed_orders_data = exec_request.get("completed_orders", [])
        completed_orders = []
        for order_data in completed_orders_data:
            completed_orders.append(Order(
                order_id=order_data.get("order_id", ""),
                unique_id=order_data.get("unique_id", ""),
                symbol=order_data.get("symbol", ""),
                direction_type=order_data.get("direction_type", 0),
                order_type=order_data.get("order_type", 0),
                qty=order_data.get("qty", 0.0),
                limit_price=order_data.get("limit_price"),
                status=order_data.get("status", 0),
                executed_size=order_data.get("executed_size", 0.0),
                avg_fill_price=order_data.get("avg_fill_price"),
                commission=order_data.get("commission"),
                cancel_reason=order_data.get("cancel_reason"),
            ))
        
        # Build Context
        context = Context(
            account=account,
            market_data_context=exec_request.get("market_data_context", []),
            incomplete_orders=incomplete_orders,
            completed_orders=completed_orders,
            strategy_params=exec_request.get("strategy_param", {}),
            exec_id=exec_request.get("exec_id", ""),
            exchange=exec_request.get("exchange", ""),
        )
        
        return context

