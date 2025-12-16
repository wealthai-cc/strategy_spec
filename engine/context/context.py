"""
Context object for strategy execution.

Provides unified interface for account, market data, and order operations.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from decimal import Decimal

# Import proto types (these would be generated from .proto files)
# For now, we'll use type hints and assume they exist


@dataclass
class Bar:
    """K-line bar data."""
    open_time: int
    close_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str


@dataclass
class Order:
    """Order object."""
    order_id: str = ""
    unique_id: str = ""
    symbol: str = ""
    direction_type: int = 0  # BUY_DIRECTION_TYPE or SELL_DIRECTION_TYPE
    order_type: int = 0  # MARKET_ORDER_TYPE or LIMIT_ORDER_TYPE
    qty: float = 0.0
    limit_price: Optional[str] = None
    status: int = 0  # OrderStatusType
    executed_size: float = 0.0
    avg_fill_price: Optional[str] = None
    commission: Optional[str] = None
    cancel_reason: Optional[str] = None


@dataclass
class Account:
    """Account information."""
    account_id: str = ""
    account_type: int = 0
    total_net_value: Optional[Dict[str, Any]] = None
    available_margin: Optional[Dict[str, Any]] = None
    margin_ratio: float = 0.0
    risk_level: float = 0.0
    leverage: float = 0.0
    balances: List[Dict[str, Any]] = field(default_factory=list)
    positions: List[Dict[str, Any]] = field(default_factory=list)


class Portfolio:
    """
    Portfolio information with JoinQuant compatibility.
    
    Supports both list and dictionary-style access to positions.
    """
    
    def __init__(self):
        """Initialize portfolio."""
        self._positions_list: List[Dict[str, Any]] = []
        self._positions_dict: Dict[str, Dict[str, Any]] = {}
        self.total_value: Optional[Dict[str, Any]] = None
        self.total_pnl: Optional[Dict[str, Any]] = None
    
    @property
    def positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get positions as dictionary (JoinQuant compatibility).
        
        Returns:
            Dictionary mapping symbol to position data
        """
        return self._positions_dict
    
    def set_positions(self, positions: List[Dict[str, Any]]) -> None:
        """
        Set positions from list and update dictionary.
        
        Args:
            positions: List of position dictionaries
        """
        self._positions_list = positions
        # Update dictionary
        self._positions_dict = {}
        for pos in positions:
            symbol = pos.get('symbol', '') if isinstance(pos, dict) else getattr(pos, 'symbol', '')
            if symbol:
                self._positions_dict[symbol] = pos
    
    def get_positions_list(self) -> List[Dict[str, Any]]:
        """
        Get positions as list (original format).
        
        Returns:
            List of position dictionaries
        """
        return self._positions_list
    
    @property
    def available_cash(self) -> float:
        """
        Get available cash for trading (JoinQuant compatibility).
        
        Calculated from account balances or available margin.
        
        Returns:
            Available cash amount
        """
        # This will be calculated from context.account
        # For now, return 0 if not set
        return getattr(self, '_available_cash', 0.0)
    
    def set_available_cash(self, value: float) -> None:
        """
        Set available cash.
        
        Args:
            value: Available cash amount
        """
        self._available_cash = value
    
    @property
    def positions_value(self) -> float:
        """
        Get total positions value (JoinQuant compatibility).
        
        Returns:
            Total market value of all positions
        """
        # This will be calculated from positions and market prices
        # For now, return 0 if not set
        return getattr(self, '_positions_value', 0.0)
    
    def set_positions_value(self, value: float) -> None:
        """
        Set positions value.
        
        Args:
            value: Total positions value
        """
        self._positions_value = value


@dataclass
class RiskEvent:
    """Risk management event."""
    risk_event_type: int = 0
    remark: str = ""


class Context:
    """
    Context object providing unified interface for strategy execution.
    
    Provides access to:
    - Account information
    - Market data (current bar, history)
    - Order operations (buy, sell, cancel)
    - Strategy parameters
    """
    
    def __init__(
        self,
        account: Account,
        market_data_context: List[Dict[str, Any]],
        incomplete_orders: List[Order],
        completed_orders: List[Order],
        strategy_params: Dict[str, str],
        exec_id: str,
        exchange: str,
    ):
        """
        Initialize Context object.
        
        Args:
            account: Account information
            market_data_context: List of market data contexts (different timeframes)
            incomplete_orders: List of incomplete orders
            completed_orders: List of completed orders
            strategy_params: Strategy parameters from ExecRequest
            exec_id: Execution ID for this execution
            exchange: Exchange name
        """
        self.account = account
        self.portfolio = Portfolio()
        self._market_data_context = market_data_context
        self._incomplete_orders = incomplete_orders
        self._completed_orders = completed_orders
        self.params = strategy_params
        self.exec_id = exec_id
        self.exchange = exchange
        
        # Current bar (latest bar from market data)
        self.current_bar: Optional[Bar] = None
        if market_data_context:
            # Get the first symbol's latest bar (assuming single symbol for now)
            first_context = market_data_context[0]
            if first_context.get("bars"):
                latest_bar_data = first_context["bars"][-1]
                self.current_bar = Bar(
                    open_time=latest_bar_data.get("open_time", 0),
                    close_time=latest_bar_data.get("close_time", 0),
                    open=latest_bar_data.get("open", "0"),
                    high=latest_bar_data.get("high", "0"),
                    low=latest_bar_data.get("low", "0"),
                    close=latest_bar_data.get("close", "0"),
                    volume=latest_bar_data.get("volume", "0"),
                )
        
        # Initialize portfolio positions from account
        self._initialize_portfolio()
        
        # Order operations collected during execution
        self._order_operations: List[Dict[str, Any]] = []
        
        # Strategy-specific storage
        self._strategy_data: Dict[str, Any] = {}
    
    def _initialize_portfolio(self) -> None:
        """Initialize portfolio from account data."""
        # Set positions from account
        if self.account and hasattr(self.account, 'positions'):
            positions_list = []
            for pos in self.account.positions:
                if isinstance(pos, dict):
                    positions_list.append(pos)
                else:
                    # Convert object to dict
                    pos_dict = {
                        'symbol': getattr(pos, 'symbol', ''),
                        'quantity': getattr(pos, 'quantity', 0),
                        'average_cost_price': getattr(pos, 'average_cost_price', None),
                        'unrealized_pnl': getattr(pos, 'unrealized_pnl', None),
                        'position_side': getattr(pos, 'position_side', None),
                    }
                    positions_list.append(pos_dict)
            self.portfolio.set_positions(positions_list)
        
        # Calculate available cash from account
        available_cash = 0.0
        if self.account:
            # Try available_margin first
            if hasattr(self.account, 'available_margin') and self.account.available_margin:
                if isinstance(self.account.available_margin, dict):
                    # Sum all available margins
                    for currency, amount in self.account.available_margin.items():
                        if isinstance(amount, (int, float)):
                            available_cash += float(amount)
                elif isinstance(self.account.available_margin, (int, float)):
                    available_cash = float(self.account.available_margin)
            
            # Fallback to balances
            if available_cash == 0.0 and hasattr(self.account, 'balances'):
                for balance in self.account.balances:
                    if isinstance(balance, dict):
                        free = balance.get('free', {})
                        if isinstance(free, dict):
                            amount = free.get('amount', 0)
                            if isinstance(amount, (int, float)):
                                available_cash += float(amount)
                        elif isinstance(free, (int, float)):
                            available_cash += float(free)
        
        self.portfolio.set_available_cash(available_cash)
        
        # Calculate positions value
        positions_value = 0.0
        for pos in self.portfolio.get_positions_list():
            if isinstance(pos, dict):
                qty = float(pos.get('quantity', 0))
                # Try to get current price from average_cost_price or use 0
                price = 0.0
                if 'average_cost_price' in pos and pos['average_cost_price']:
                    if isinstance(pos['average_cost_price'], dict):
                        price = float(list(pos['average_cost_price'].values())[0] if pos['average_cost_price'] else 0)
                    elif isinstance(pos['average_cost_price'], (int, float)):
                        price = float(pos['average_cost_price'])
                # For now, use average cost price as approximation
                # In real implementation, should use current market price
                positions_value += qty * price
        
        self.portfolio.set_positions_value(positions_value)
    
    @property
    def current_dt(self) -> Optional[datetime]:
        """
        Get current datetime (JoinQuant compatibility).
        
        Returns:
            datetime object representing current bar's time, or None if no current_bar
        """
        if self.current_bar is None:
            return None
        
        # Convert close_time (Unix timestamp in milliseconds) to datetime
        close_time_ms = self.current_bar.close_time
        if close_time_ms == 0:
            return None
        
        return datetime.fromtimestamp(close_time_ms / 1000.0)
    
    def __getattr__(self, name: str) -> Any:
        """Allow strategy to store custom data on context."""
        if name in self._strategy_data:
            return self._strategy_data[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Allow strategy to store custom data on context."""
        # Check if it's a known attribute
        known_attrs = {
            "account", "portfolio", "_market_data_context", "_incomplete_orders",
            "_completed_orders", "params", "exec_id", "exchange", "current_bar",
            "current_dt", "_order_operations", "_strategy_data"
        }
        if name not in known_attrs and not name.startswith("_"):
            # Store in strategy data
            if not hasattr(self, "_strategy_data"):
                super().__setattr__("_strategy_data", {})
            self._strategy_data[name] = value
        else:
            super().__setattr__(name, value)
    
    def history(
        self,
        symbol: str,
        count: int,
        timeframe: str
    ) -> List[Bar]:
        """
        Get historical bar data.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            count: Number of bars to retrieve
            timeframe: Time resolution (e.g., "1h", "1d")
        
        Returns:
            List of Bar objects, ordered by time (oldest first)
        """
        # Find matching market data context
        for context in self._market_data_context:
            if (context.get("symbol") == symbol and 
                context.get("timeframe") == timeframe):
                bars_data = context.get("bars", [])
                # Return last 'count' bars
                bars = []
                for bar_data in bars_data[-count:]:
                    bars.append(Bar(
                        open_time=bar_data.get("open_time", 0),
                        close_time=bar_data.get("close_time", 0),
                        open=bar_data.get("open", "0"),
                        high=bar_data.get("high", "0"),
                        low=bar_data.get("low", "0"),
                        close=bar_data.get("close", "0"),
                        volume=bar_data.get("volume", "0"),
                    ))
                return bars
        
        # Return empty list if not found
        return []
    
    def order_buy(
        self,
        symbol: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Order:
        """
        Place a buy order.
        
        Args:
            symbol: Trading pair
            quantity: Order quantity
            price: Limit price (optional, None for market order)
        
        Returns:
            Order object
        """
        return self._create_order(
            symbol=symbol,
            quantity=quantity,
            direction_type=1,  # BUY_DIRECTION_TYPE
            price=price
        )
    
    def order_sell(
        self,
        symbol: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Order:
        """
        Place a sell order.
        
        Args:
            symbol: Trading pair
            quantity: Order quantity
            price: Limit price (optional, None for market order)
        
        Returns:
            Order object
        """
        return self._create_order(
            symbol=symbol,
            quantity=quantity,
            direction_type=2,  # SELL_DIRECTION_TYPE
            price=price
        )
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID or unique_id
        
        Returns:
            True if cancellation request was added, False otherwise
        """
        # Check if order exists in incomplete orders
        order_found = False
        for order in self._incomplete_orders:
            if order.order_id == order_id or order.unique_id == order_id:
                order_found = True
                break
        
        if not order_found:
            return False
        
        # Add cancel operation
        self._order_operations.append({
            "order_op_type": 2,  # WITHDRAW_ORDER_OP_TYPE
            "order": {
                "order_id": order_id,
            }
        })
        return True
    
    def _create_order(
        self,
        symbol: str,
        quantity: float,
        direction_type: int,
        price: Optional[float] = None
    ) -> Order:
        """Internal method to create an order."""
        # Generate unique_id for order
        unique_id = f"{self.exec_id}_{uuid.uuid4().hex[:8]}"
        
        # Determine order type
        if price is not None:
            order_type = 2  # LIMIT_ORDER_TYPE
        else:
            order_type = 1  # MARKET_ORDER_TYPE
        
        # Create order object
        order = Order(
            unique_id=unique_id,
            symbol=symbol,
            direction_type=direction_type,
            order_type=order_type,
            qty=quantity,
            limit_price=str(price) if price is not None else None,
            status=1,  # NEW_ORDER_STATUS_TYPE
        )
        
        # Add order operation
        self._order_operations.append({
            "order_op_type": 1,  # CREATE_ORDER_OP_TYPE
            "order": {
                "unique_id": order.unique_id,
                "symbol": order.symbol,
                "direction_type": order.direction_type,
                "order_type": order.order_type,
                "qty": order.qty,
                "limit_price": order.limit_price,
                "time_in_force": 2,  # GTC_TIME_IN_FORCE_TYPE
            }
        })
        
        return order
    
    def get_order_operations(self) -> List[Dict[str, Any]]:
        """
        Get collected order operations.
        
        Returns:
            List of order operation dictionaries
        """
        return self._order_operations.copy()

