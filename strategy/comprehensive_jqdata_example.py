"""
综合示例 - 展示所有 wealthdata API 的使用

这个策略示例展示了如何使用所有 wealthdata API，
包括价格数据、证券信息、指数、财务数据和行业分类。
"""

import wealthdata


def initialize(context):
    """策略初始化"""
    context.symbol = "BTCUSDT"
    context.ma_period = 20
    context.quantity = 0.1


def handle_bar(context, bar):
    """
    综合使用各种 wealthdata API
    """
    print("=" * 60)
    print("wealthdata API 综合示例")
    print("=" * 60)
    
    # 1. 获取价格数据
    print("\n1. 获取价格数据 (get_price):")
    df_price = wealthdata.get_price(context.symbol, count=context.ma_period, frequency='1h')
    print(f"   获取到 {len(df_price)} 根 K 线")
    if len(df_price) > 0:
        ma = df_price['close'].mean()
        print(f"   移动平均: {ma:.2f}")
    
    # 2. 获取所有交易对
    print("\n2. 获取所有交易对 (get_all_securities):")
    all_securities = wealthdata.get_all_securities()
    print(f"   可用交易对数量: {len(all_securities)}")
    if len(all_securities) > 0:
        print(f"   前 5 个交易对: {list(all_securities.index[:5])}")
    
    # 3. 获取交易日
    print("\n3. 获取交易日 (get_trade_days):")
    trade_days = wealthdata.get_trade_days(count=7)
    print(f"   最近 7 天: {trade_days}")
    
    # 4. 获取指数成分
    print("\n4. 获取指数成分 (get_index_stocks):")
    btc_index_stocks = wealthdata.get_index_stocks('BTC_INDEX')
    print(f"   BTC 指数成分: {btc_index_stocks}")
    
    # 5. 获取指数权重
    print("\n5. 获取指数权重 (get_index_weights):")
    btc_index_weights = wealthdata.get_index_weights('BTC_INDEX')
    print(f"   BTC 指数权重:")
    for symbol, row in btc_index_weights.iterrows():
        print(f"     {symbol}: {row['weight']:.2%}")
    
    # 6. 获取财务数据（简化）
    print("\n6. 获取财务数据 (get_fundamentals):")
    fundamentals = wealthdata.get_fundamentals({'code': context.symbol})
    if len(fundamentals) > 0:
        print(f"   财务数据: {fundamentals.to_dict('records')}")
    else:
        print("   (财务数据不适用于加密货币)")
    
    # 7. 获取行业分类
    print("\n7. 获取行业分类 (get_industry):")
    industry = wealthdata.get_industry(context.symbol)
    print(f"   {context.symbol} 的行业分类: {industry}")
    
    # 策略逻辑：简单的移动平均策略
    if len(df_price) >= context.ma_period:
        current_price = float(bar.close)
        if current_price > ma:
            # 检查是否已有持仓
            has_position = any(
                p.get("symbol") == context.symbol and float(p.get("quantity", 0)) > 0
                for p in context.account.positions
            )
            if not has_position:
                context.order_buy(context.symbol, context.quantity, price=current_price)
        elif current_price < ma:
            # 卖出持仓
            for position in context.account.positions:
                if position.get("symbol") == context.symbol:
                    quantity = float(position.get("quantity", 0))
                    if quantity > 0:
                        context.order_sell(context.symbol, quantity, price=current_price)
                        break
    
    print("=" * 60)


def on_order(context, order):
    """处理订单状态变更"""
    if order.status == 3:  # FILLED
        industry = wealthdata.get_industry(order.symbol)
        print(f"订单成交: {order.symbol} ({industry}), 价格: {order.avg_fill_price}")



