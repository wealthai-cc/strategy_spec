"""
测试策略脚本

用于快速测试和验证策略文件是否能正确加载和执行。
"""

import sys
from pathlib import Path

# 添加 engine 到路径
sys.path.insert(0, str(Path(__file__).parent))

from engine.engine import StrategyExecutionEngine


def test_strategy(strategy_path: str):
    """测试策略文件"""
    print(f"正在测试策略: {strategy_path}")
    print("=" * 60)
    
    try:
        # 创建引擎
        engine = StrategyExecutionEngine(strategy_path)
        print("✅ 策略加载成功")
        
        # 准备测试数据
        exec_request = {
            "trigger_type": 1,  # MARKET_DATA_TRIGGER_TYPE
            "trigger_detail": {},
            "market_data_context": [{
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "bars": [
                    {
                        "open_time": 1000000,
                        "close_time": 1003600000,  # 1小时后
                        "open": "49000.0",
                        "high": "51000.0",
                        "low": "48000.0",
                        "close": "50500.0",  # 价格高于 50000，应该触发买入
                        "volume": "1000.0",
                    },
                    {
                        "open_time": 1003600000,
                        "close_time": 1007200000,  # 2小时后
                        "open": "50500.0",
                        "high": "52000.0",
                        "low": "50000.0",
                        "close": "51500.0",
                        "volume": "1100.0",
                    },
                ]
            }],
            "account": {
                "account_id": "test_account_001",
                "account_type": 1,  # SIMULATE_ACCOUNT_TYPE
                "balances": [
                    {
                        "currency_type": 1,  # USDT
                        "amount": 10000.0,
                    }
                ],
                "positions": [],
                "total_net_value": {
                    "currency_type": 1,
                    "amount": 10000.0,
                },
                "available_margin": {
                    "currency_type": 1,
                    "amount": 10000.0,
                },
                "margin_ratio": 0.0,
                "risk_level": 0.0,
                "leverage": 1.0,
            },
            "incomplete_orders": [],
            "completed_orders": [],
            "exchange": "binance",
            "exec_id": "test_exec_001",
            "strategy_param": {
                "ma_period": "20",
                "quantity": "0.1",
            },
        }
        
        # 执行策略
        print("\n执行策略...")
        response = engine.execute(exec_request)
        
        # 显示结果
        print("\n" + "=" * 60)
        print("执行结果:")
        print(f"  状态: {response['status']} (0=成功, 1=部分成功, 2=失败)")
        
        if response['status'] == 0:
            print("  ✅ 执行成功")
        else:
            print(f"  ❌ 执行失败: {response.get('error_message', '未知错误')}")
        
        # 显示订单操作
        order_ops = response.get('order_op_event', [])
        print(f"\n订单操作数量: {len(order_ops)}")
        for i, op in enumerate(order_ops, 1):
            op_type = op.get('order_op_type', 0)
            op_type_name = {
                1: "创建订单",
                2: "撤销订单",
                3: "修改订单",
            }.get(op_type, "未知操作")
            
            print(f"  操作 {i}: {op_type_name}")
            if 'order' in op:
                order = op['order']
                print(f"    订单ID: {order.get('unique_id', 'N/A')}")
                print(f"    品种: {order.get('symbol', 'N/A')}")
                print(f"    数量: {order.get('qty', 'N/A')}")
                if order.get('limit_price'):
                    print(f"    限价: {order.get('limit_price')}")
        
        # 显示警告
        warnings = response.get('warnings', [])
        if warnings:
            print(f"\n警告 ({len(warnings)}):")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        
        print("\n" + "=" * 60)
        return response['status'] == 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 默认测试 simple_strategy.py
    if len(sys.argv) > 1:
        strategy_path = sys.argv[1]
    else:
        strategy_path = "strategy/simple_strategy.py"
    
    success = test_strategy(strategy_path)
    sys.exit(0 if success else 1)

