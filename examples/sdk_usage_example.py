"""
WealthAI SDK 使用示例

演示如何使用 wealthai_sdk 进行交易规则查询、佣金计算等操作
"""

from wealthai_sdk import (
    get_trading_rule, 
    get_commission_rates, 
    bars_to_dataframe,
    NotFoundError, 
    ParseError
)


def example_trading_rule_validation():
    """示例：下单前参数校验"""
    print("=== 交易规则校验示例 ===")
    
    try:
        # 获取交易规则
        rule = get_trading_rule("binance", "BTCUSDT")
        print(f"BTCUSDT 交易规则: {rule}")
        
        # 模拟订单参数
        target_quantity = 0.123456789
        target_price = 42000.123
        
        # 校验数量
        min_qty = rule["min_quantity"]
        quantity_step = rule["quantity_step"]
        quantity_precision = rule["quantity_precision"]
        
        # 调整数量
        adjusted_qty = max(target_quantity, min_qty)  # 不小于最小数量
        adjusted_qty = round(adjusted_qty / quantity_step) * quantity_step  # 符合步进
        adjusted_qty = round(adjusted_qty, quantity_precision)  # 符合精度
        
        print(f"原始数量: {target_quantity}")
        print(f"调整后数量: {adjusted_qty}")
        
        # 校验价格精度
        price_precision = rule["price_precision"]
        adjusted_price = round(target_price, price_precision)
        
        print(f"原始价格: {target_price}")
        print(f"调整后价格: {adjusted_price}")
        
    except NotFoundError as e:
        print(f"错误: {e}")
    except ParseError as e:
        print(f"解析错误: {e}")


def example_commission_calculation():
    """示例：佣金计算"""
    print("\n=== 佣金计算示例 ===")
    
    try:
        # 获取佣金费率
        fees = get_commission_rates("binance", "BTCUSDT")
        print(f"BTCUSDT 佣金费率: {fees}")
        
        # 计算交易成本
        order_amount = 10000.0  # 订单金额 $10,000
        
        # Maker 订单（限价单）
        maker_commission = order_amount * fees["maker_fee_rate"]
        print(f"Maker 订单佣金: ${maker_commission:.2f} ({fees['maker_fee_rate']*100:.3f}%)")
        
        # Taker 订单（市价单）
        taker_commission = order_amount * fees["taker_fee_rate"]
        print(f"Taker 订单佣金: ${taker_commission:.2f} ({fees['taker_fee_rate']*100:.3f}%)")
        
    except NotFoundError as e:
        print(f"错误: {e}")
    except ParseError as e:
        print(f"解析错误: {e}")


def example_leverage_check():
    """示例：杠杆限制检查"""
    print("\n=== 杠杆限制检查示例 ===")
    
    try:
        rule = get_trading_rule("binance", "BTCUSDT")
        max_leverage = rule.get("max_leverage", 1.0)
        
        target_leverages = [1.0, 10.0, 50.0, 100.0, 150.0]
        
        for leverage in target_leverages:
            if leverage <= max_leverage:
                print(f"杠杆 {leverage}x: ✅ 允许 (最大 {max_leverage}x)")
            else:
                print(f"杠杆 {leverage}x: ❌ 超限 (最大 {max_leverage}x)")
                
    except NotFoundError as e:
        print(f"错误: {e}")


def example_dataframe_conversion():
    """示例：DataFrame 转换"""
    print("\n=== DataFrame 转换示例 ===")
    
    # 模拟 Bar 数据（通常来自 context.history()）
    class MockBar:
        def __init__(self, open_price, high, low, close, volume, close_time):
            self.open = open_price
            self.high = high
            self.low = low
            self.close = close
            self.volume = volume
            self.close_time = close_time
    
    # 创建模拟数据
    bars = [
        MockBar(42000.0, 42500.0, 41500.0, 42200.0, 1000.0, 1640995200),
        MockBar(42200.0, 42800.0, 41800.0, 42600.0, 1200.0, 1640998800),
        MockBar(42600.0, 43000.0, 42000.0, 42400.0, 1100.0, 1641002400),
    ]
    
    # 转换为 DataFrame
    df = bars_to_dataframe(bars)
    print("转换后的 DataFrame:")
    print(df)
    
    # 使用 pandas 进行技术分析
    print(f"\n技术指标:")
    print(f"平均价格: ${df['close'].mean():.2f}")
    print(f"最高价: ${df['high'].max():.2f}")
    print(f"最低价: ${df['low'].min():.2f}")
    print(f"总成交量: {df['volume'].sum():.0f}")


def example_error_handling():
    """示例：错误处理"""
    print("\n=== 错误处理示例 ===")
    
    # 测试不存在的交易所
    try:
        get_trading_rule("unknown_exchange", "BTCUSDT")
    except NotFoundError as e:
        print(f"预期错误 - 不存在的交易所: {e}")
    
    # 测试不存在的交易品种
    try:
        get_trading_rule("binance", "UNKNOWN_SYMBOL")
    except NotFoundError as e:
        print(f"预期错误 - 不存在的品种: {e}")


if __name__ == "__main__":
    """运行所有示例"""
    print("WealthAI SDK 使用示例")
    print("=" * 50)
    
    example_trading_rule_validation()
    example_commission_calculation()
    example_leverage_check()
    example_dataframe_conversion()
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("示例运行完成！")
    print("\n提示：")
    print("- 确保配置文件存在于 config/ 目录")
    print("- 可以通过环境变量 WEALTHAI_CONFIG_DIR 指定配置目录")
    print("- 查看 config/README.md 了解配置文件格式")