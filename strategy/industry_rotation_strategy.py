"""
行业轮动策略示例 - 使用 wealthdata 新 API

这个策略展示如何使用 get_all_securities(), get_industry() 等 API
来构建基于行业分类的轮动策略。
"""

import wealthdata


def initialize(context):
    """策略初始化"""
    context.target_industries = ['Layer1', 'DeFi', 'Layer2']  # 关注的行业
    context.industry_count = 2  # 每个行业选择的交易对数量
    context.quantity_per_pair = 0.1  # 每个交易对的持仓数量


def handle_bar(context, bar):
    """
    处理 K 线数据，执行行业轮动策略
    """
    # 获取所有可用交易对
    all_securities = wealthdata.get_all_securities()
    
    if len(all_securities) == 0:
        return  # 没有可用交易对
    
    # 按行业分类交易对
    industry_pairs = {}
    for symbol in all_securities.index:
        industry = wealthdata.get_industry(symbol)
        if industry in context.target_industries:
            if industry not in industry_pairs:
                industry_pairs[industry] = []
            industry_pairs[industry].append(symbol)
    
    # 为每个行业选择表现最好的交易对（简化示例：选择价格涨幅最大的）
    selected_pairs = []
    for industry, pairs in industry_pairs.items():
        # 获取每个交易对的价格数据
        pair_performance = []
        for symbol in pairs[:10]:  # 限制检查数量
            try:
                bars = context.history(symbol, 2, "1h")
                if len(bars) >= 2:
                    price_change = (float(bars[-1].close) - float(bars[0].close)) / float(bars[0].close)
                    pair_performance.append((symbol, price_change))
            except:
                continue
        
        # 选择涨幅最大的 N 个
        pair_performance.sort(key=lambda x: x[1], reverse=True)
        selected_pairs.extend([p[0] for p in pair_performance[:context.industry_count]])
    
    # 平仓不在选择列表中的持仓
    for position in context.account.positions:
        symbol = position.get("symbol")
        quantity = float(position.get("quantity", 0))
        if quantity > 0 and symbol not in selected_pairs:
            context.order_sell(symbol, quantity)
    
    # 买入选择的交易对（如果还没有持仓）
    for symbol in selected_pairs:
        has_position = any(
            p.get("symbol") == symbol and float(p.get("quantity", 0)) > 0
            for p in context.account.positions
        )
        if not has_position:
            bars = context.history(symbol, 1, "1h")
            if bars:
                current_price = float(bars[0].close)
                context.order_buy(symbol, context.quantity_per_pair, price=current_price)


def on_order(context, order):
    """处理订单状态变更"""
    if order.status == 3:  # FILLED
        industry = wealthdata.get_industry(order.symbol)
        print(f"订单成交: {order.symbol} ({industry}), 数量: {order.executed_size}")

