"""
JoinQuant 迁移示例策略

这个示例展示如何将 JoinQuant 策略代码迁移到我们的框架。
只需要修改 import 语句，其他代码完全不变。
"""

# 原来的代码：import jqdatasdk
# 迁移后：import wealthdata
import wealthdata


def initialize(context):
    """策略初始化"""
    # 只需要修改交易品种格式（股票代码 → 交易对）
    # 原来：context.symbol = '000001.XSHE'
    context.symbol = 'BTCUSDT'  # 加密货币交易对格式
    
    # 其他代码完全不变
    context.ma_period = 20
    context.quantity = 0.1


def handle_bar(context, bar):
    """
    处理 K 线数据
    
    注意：这里的代码与 JoinQuant 完全一致，无需修改！
    """
    # 使用 wealthdata.get_price() - 与 jqdatasdk.get_price() 接口完全一致
    df = wealthdata.get_price(context.symbol, count=context.ma_period, frequency='1h')
    
    # pandas DataFrame 操作 - 完全不变
    ma = df['close'].mean()
    current_price = float(bar.close)
    
    # 策略逻辑 - 完全不变
    if current_price > ma:
        # 下单 API 需要调整：order_buy() → context.order_buy()
        context.order_buy(context.symbol, context.quantity, price=current_price)
    elif current_price < ma:
        # 检查是否有持仓
        for position in context.account.positions:
            if position.get("symbol") == context.symbol and position.get("quantity", 0) > 0:
                context.order_sell(context.symbol, position.get("quantity", 0), price=current_price)
                break


def on_order(context, order):
    """处理订单状态变更"""
    if order.status == 3:  # FILLED
        print(f"订单成交: {order.order_id}, 成交价: {order.avg_fill_price}")
    elif order.status == 4:  # CANCELED
        print(f"订单取消: {order.order_id}, 原因: {order.cancel_reason}")

