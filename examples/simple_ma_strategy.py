"""
Simple Moving Average Strategy Example

This is a simple example strategy that uses moving averages to make trading decisions.
"""


def initialize(context):
    """Initialize strategy parameters."""
    context.symbol = "BTCUSDT"
    context.ma_short = 5
    context.ma_long = 20
    context.quantity = 0.1


def handle_bar(context, bar):
    """Handle new bar data."""
    # Get historical data
    bars = context.history(context.symbol, context.ma_long, "1h")
    
    if len(bars) < context.ma_long:
        return  # Not enough data
    
    # Calculate moving averages (simplified)
    # In real implementation, you would use proper MA calculation
    short_ma = sum(float(b.close) for b in bars[-context.ma_short:]) / context.ma_short
    long_ma = sum(float(b.close) for b in bars) / context.ma_long
    
    current_price = float(bar.close)
    
    # Trading logic: buy when short MA crosses above long MA
    if current_price > short_ma > long_ma:
        # Check if we already have a position
        has_position = any(
            p.get("symbol") == context.symbol and p.get("quantity", 0) > 0
            for p in context.account.positions
        )
        
        if not has_position:
            # Buy signal
            context.order_buy(context.symbol, context.quantity, price=current_price)
    
    # Sell when short MA crosses below long MA
    elif current_price < short_ma < long_ma:
        # Check if we have a position to sell
        for position in context.account.positions:
            if position.get("symbol") == context.symbol and position.get("quantity", 0) > 0:
                # Sell signal
                context.order_sell(context.symbol, position.get("quantity", 0), price=current_price)
                break


def on_order(context, order):
    """Handle order status changes."""
    if order.status == 3:  # FILLED
        print(f"Order filled: {order.order_id}, Price: {order.avg_fill_price}")
    elif order.status == 4:  # CANCELED
        print(f"Order canceled: {order.order_id}, Reason: {order.cancel_reason}")
    elif order.status == 6:  # REJECTED
        print(f"Order rejected: {order.order_id}")


def on_risk_event(context, event):
    """Handle risk management events."""
    if event.risk_event_type == 1:  # MARGIN_CALL_EVENT_TYPE
        # Reduce position if risk level is too high
        if context.account.risk_level > 80:
            for position in context.account.positions:
                if position.get("symbol") == context.symbol:
                    reduce_qty = position.get("quantity", 0) * 0.5
                    if reduce_qty > 0:
                        context.order_sell(context.symbol, reduce_qty)

