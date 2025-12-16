#!/usr/bin/env python3
"""
简单的 SDK 测试脚本
"""

try:
    print("开始测试 WealthAI SDK...")
    
    # 测试导入
    from wealthai_sdk import get_trading_rule, get_commission_rates, bars_to_dataframe
    print("✅ SDK 导入成功")
    
    # 测试交易规则查询
    try:
        rule = get_trading_rule("binance", "BTCUSDT")
        print(f"✅ 交易规则查询成功: {rule}")
    except Exception as e:
        print(f"❌ 交易规则查询失败: {e}")
    
    # 测试佣金费率查询
    try:
        fees = get_commission_rates("binance", "BTCUSDT")
        print(f"✅ 佣金费率查询成功: {fees}")
    except Exception as e:
        print(f"❌ 佣金费率查询失败: {e}")
    
    # 测试 DataFrame 转换
    try:
        class MockBar:
            def __init__(self, open_price, high, low, close, volume, close_time):
                self.open = open_price
                self.high = high
                self.low = low
                self.close = close
                self.volume = volume
                self.close_time = close_time
        
        bars = [MockBar(100, 105, 95, 102, 1000, 1640995200)]
        df = bars_to_dataframe(bars)
        print(f"✅ DataFrame 转换成功: {len(df)} 行数据")
    except Exception as e:
        print(f"❌ DataFrame 转换失败: {e}")
    
    print("\n🎉 所有测试完成！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()