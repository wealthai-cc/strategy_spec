"""
Order functions for JoinQuant compatibility (order_value, order_target).
"""

from typing import Optional, Dict, Callable, Any
from engine.wealthdata.wealthdata import get_context
from engine.compat.market_type import detect_market_type, MarketType


def create_order_functions() -> Dict[str, Callable]:
    """
    Create order functions for strategy use.
    
    Returns:
        Dictionary with 'order_value' and 'order_target' functions
    """
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
        if abs(diff) < 1e-8:  # Already at target (accounting for floating point)
            return None
        elif diff > 0:
            # Need to buy more
            # For stock markets, diff is already an integer, so it should be >= 1 if > 0
            # For crypto markets, allow fractional quantities
            return context.order_buy(symbol, diff, price)
        else:
            # Need to sell (diff < 0)
            sell_qty = abs(diff)
            # For stock markets, sell_qty is already an integer, so it should be >= 1 if > 0
            # For crypto markets, allow fractional quantities
            return context.order_sell(symbol, sell_qty, price)
    
    return {
        'order_value': order_value,
        'order_target': order_target,
    }


def _get_position_qty(context: Any, symbol: str) -> float:
    """
    Get current position quantity for a symbol.
    
    Args:
        context: Context object
        symbol: Trading symbol
    
    Returns:
        Current position quantity (0 if no position)
    """
    # Check portfolio positions
    if hasattr(context, 'portfolio') and hasattr(context.portfolio, 'positions'):
        positions = context.portfolio.positions
        if isinstance(positions, dict):
            # Dictionary-style access
            if symbol in positions:
                pos = positions[symbol]
                if isinstance(pos, dict):
                    return float(pos.get('quantity', 0))
                return float(getattr(pos, 'quantity', 0))
        elif isinstance(positions, list):
            # List-style access
            for pos in positions:
                pos_symbol = pos.get('symbol', '') if isinstance(pos, dict) else getattr(pos, 'symbol', '')
                if pos_symbol == symbol:
                    qty = pos.get('quantity', 0) if isinstance(pos, dict) else getattr(pos, 'quantity', 0)
                    return float(qty)
    
    # Check account positions
    if hasattr(context, 'account') and hasattr(context.account, 'positions'):
        for pos in context.account.positions:
            pos_symbol = pos.get('symbol', '') if isinstance(pos, dict) else getattr(pos, 'symbol', '')
            if pos_symbol == symbol:
                qty = pos.get('quantity', 0) if isinstance(pos, dict) else getattr(pos, 'quantity', 0)
                return float(qty)
    
    return 0.0

