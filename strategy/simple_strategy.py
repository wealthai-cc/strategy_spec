"""
最简单的策略示例 - 用于验证框架功能

这是一个最简单的策略，用于验证引擎是否能正确加载和执行策略。
"""


def initialize(context):
    """策略初始化 - 必需函数"""
    # 设置交易品种
    context.symbol = "BTCUSDT"
    
    # 设置交易数量
    context.quantity = 0.1
    
    # 可以存储任何自定义数据
    context.order_count = 0
    print(f"策略初始化完成，交易品种: {context.symbol}")


def handle_bar(context, bar):
    """
    处理新 K 线数据 - 可选函数
    
    当收到新的 K 线数据时，这个函数会被调用
    """
    current_price = float(bar.close)
    print(f"收到新 K 线: {context.symbol}, 价格: {current_price}, 时间: {bar.close_time}")
    
    # 简单的策略逻辑：价格大于某个值就买入
    # 这只是示例，实际策略会更复杂
    if current_price > 50000 and context.order_count == 0:
        print(f"触发买入信号，价格: {current_price}")
        order = context.order_buy(context.symbol, context.quantity, price=current_price)
        context.order_count += 1
        print(f"已下单: {order.unique_id}")


def on_order(context, order):
    """
    处理订单状态变更 - 可选函数
    
    当订单状态发生变化时（成交、取消、拒绝等），这个函数会被调用
    """
    if order.status == 3:  # FILLED - 订单成交
        print(f"✅ 订单成交: {order.order_id}, 成交价: {order.avg_fill_price}, 数量: {order.executed_size}")
    elif order.status == 4:  # CANCELED - 订单取消
        print(f"❌ 订单取消: {order.order_id}, 原因: {order.cancel_reason}")
    elif order.status == 6:  # REJECTED - 订单拒绝
        print(f"⚠️  订单拒绝: {order.order_id}")

