"""
指数策略示例 - 使用 wealthdata 新 API

这个策略展示如何使用 get_index_stocks() 和 get_index_weights() 
来构建基于指数的投资组合策略。
"""

import wealthdata


def initialize(context):
    """策略初始化"""
    context.index_symbol = 'BTC_INDEX'  # 使用 BTC 指数
    context.rebalance_threshold = 0.05  # 权重偏差阈值（5%）


def handle_bar(context, bar):
    """
    处理 K 线数据，执行指数跟踪策略
    """
    # 获取指数成分和权重
    index_stocks = wealthdata.get_index_stocks(context.index_symbol)
    index_weights = wealthdata.get_index_weights(context.index_symbol)
    
    if len(index_stocks) == 0 or len(index_weights) == 0:
        return  # 指数数据不可用
    
    # 计算当前持仓权重
    total_value = float(context.account.total_net_value.get("amount", 0))
    if total_value == 0:
        return
    
    current_weights = {}
    for position in context.account.positions:
        symbol = position.get("symbol")
        quantity = float(position.get("quantity", 0))
        if symbol in index_stocks and quantity > 0:
            # 获取当前价格（简化，使用 bar 的价格）
            current_price = float(bar.close) if bar.symbol == symbol else 0
            if current_price > 0:
                position_value = quantity * current_price
                current_weights[symbol] = position_value / total_value
    
    # 对比目标权重，执行再平衡
    for symbol in index_stocks:
        target_weight = index_weights.loc[symbol, 'weight'] if symbol in index_weights.index else 0
        current_weight = current_weights.get(symbol, 0)
        
        weight_diff = target_weight - current_weight
        
        # 如果偏差超过阈值，进行再平衡
        if abs(weight_diff) > context.rebalance_threshold:
            target_value = total_value * target_weight
            current_value = total_value * current_weight
            adjust_value = target_value - current_value
            
            # 获取当前价格
            bars = context.history(symbol, 1, "1h")
            if bars:
                current_price = float(bars[0].close)
                adjust_quantity = adjust_value / current_price
                
                if adjust_quantity > 0:
                    # 买入
                    context.order_buy(symbol, abs(adjust_quantity), price=current_price)
                elif adjust_quantity < 0:
                    # 卖出
                    context.order_sell(symbol, abs(adjust_quantity), price=current_price)


def on_order(context, order):
    """处理订单状态变更"""
    if order.status == 3:  # FILLED
        print(f"订单成交: {order.symbol}, 数量: {order.executed_size}, 价格: {order.avg_fill_price}")

