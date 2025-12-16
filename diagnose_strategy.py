"""
策略诊断工具

用于诊断策略执行问题，帮助区分是测试文件、框架还是策略的问题。
"""

import sys
from pathlib import Path
from datetime import datetime
import traceback

sys.path.insert(0, str(Path(__file__).parent))

from engine.engine import StrategyExecutionEngine
from engine.context.context import Account
from engine.compat.scheduler import get_scheduled_functions
from engine.compat.market_time import is_time_match
from engine.compat.market_type import detect_market_type, MarketType


def diagnose_strategy(strategy_path: str):
    """诊断策略执行问题"""
    print("=" * 80)
    print("策略诊断报告")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    try:
        # 1. 检查策略文件是否存在
        print("\n[1] 检查策略文件...")
        if not Path(strategy_path).exists():
            issues.append(f"❌ 策略文件不存在: {strategy_path}")
            print(f"  ❌ 文件不存在")
            return
        print(f"  ✓ 文件存在: {strategy_path}")
        
        # 2. 加载策略
        print("\n[2] 加载策略...")
        try:
            engine = StrategyExecutionEngine(strategy_path)
            engine.load_strategy()
            print("  ✓ 策略加载成功")
        except Exception as e:
            issues.append(f"❌ 策略加载失败: {e}")
            print(f"  ❌ 加载失败: {e}")
            traceback.print_exc()
            return
        
        strategy_module = engine.loader._module
        
        # 3. 检查函数注入
        print("\n[3] 检查兼容函数注入...")
        required_funcs = ['g', 'log', 'run_daily', 'order_value', 'order_target',
                          'set_benchmark', 'set_option', 'set_order_cost']
        for func_name in required_funcs:
            if hasattr(strategy_module, func_name):
                print(f"  ✓ {func_name}")
            else:
                issues.append(f"❌ 函数未注入: {func_name}")
                print(f"  ❌ {func_name} (未注入)")
        
        # 4. 检查 wealthdata
        print("\n[4] 检查 wealthdata 模块...")
        try:
            import wealthdata
            wealthdata_funcs = ['get_price', 'get_bars', 'get_trades']
            for func_name in wealthdata_funcs:
                if hasattr(wealthdata, func_name):
                    print(f"  ✓ wealthdata.{func_name}")
                else:
                    issues.append(f"❌ wealthdata.{func_name} 未实现")
                    print(f"  ❌ wealthdata.{func_name} (未实现)")
        except ImportError as e:
            issues.append(f"❌ wealthdata 模块导入失败: {e}")
            print(f"  ❌ wealthdata 导入失败")
        
        # 5. 检查策略函数
        print("\n[5] 检查策略生命周期函数...")
        lifecycle_funcs = ['initialize', 'before_trading', 'handle_bar', 
                          'on_order', 'on_risk_event']
        for func_name in lifecycle_funcs:
            if engine.loader.has_function(func_name):
                print(f"  ✓ {func_name}")
            else:
                if func_name == 'initialize':
                    issues.append(f"❌ 必需函数缺失: {func_name}")
                    print(f"  ❌ {func_name} (必需)")
                else:
                    print(f"  - {func_name} (可选，未定义)")
        
        # 6. 检查 run_daily 注册
        print("\n[6] 检查 run_daily 注册...")
        exec_request = {
            'trigger_type': 1,
            'trigger_detail': {},
            'market_data_context': [{
                'symbol': '000001.XSHE',
                'timeframe': '1d',
                'bars': [{
                    'open_time': int(datetime.now().timestamp() * 1000),
                    'close_time': int(datetime.now().timestamp() * 1000),
                    'open': '10.0', 'high': '11.0', 'low': '9.0', 
                    'close': '10.5', 'volume': '1000',
                }]
            }],
            'account': Account(account_id='test', available_margin={'USDT': 10000.0}),
            'incomplete_orders': [],
            'completed_orders': [],
            'exchange': 'binance',
            'exec_id': 'diagnose',
            'strategy_param': {},
        }
        
        context = engine._build_context(exec_request)
        engine.lifecycle.initialize(context)
        
        scheduled = get_scheduled_functions(strategy_module)
        print(f"  注册的定时函数数量: {len(scheduled)}")
        if len(scheduled) == 0:
            warnings.append("⚠️  没有注册任何定时函数（run_daily）")
            print("  ⚠️  没有注册定时函数")
        else:
            for s in scheduled:
                print(f"    - {s['func'].__name__} at {s['time']} (ref: {s.get('reference_security', 'N/A')})")
        
        # 7. 检查时间匹配
        print("\n[7] 检查时间匹配...")
        current_time = datetime.utcnow()
        if scheduled:
            for s in scheduled:
                time_point = s.get('time', 'open')
                ref_security = s.get('reference_security')
                
                # 检测市场类型
                market_type = MarketType.CRYPTO
                if ref_security:
                    market_type = detect_market_type(ref_security, context)
                
                matches = is_time_match(current_time, market_type, time_point, tolerance_minutes=30)
                status = "✓" if matches else "✗"
                print(f"  {status} {s['func'].__name__} ({time_point}) - 市场: {market_type.value}, 匹配: {matches}")
                if not matches:
                    warnings.append(f"⚠️  {s['func'].__name__} 时间不匹配（当前时间可能不在触发窗口内）")
        
        # 8. 检查数据
        print("\n[8] 检查市场数据...")
        market_data = exec_request['market_data_context']
        if not market_data:
            issues.append("❌ 没有提供市场数据")
            print("  ❌ 没有市场数据")
        else:
            for md in market_data:
                symbol = md.get('symbol', 'N/A')
                bars = md.get('bars', [])
                print(f"  ✓ {symbol}: {len(bars)} 根K线")
                if len(bars) < 5:
                    warnings.append(f"⚠️  {symbol} 只有 {len(bars)} 根K线，策略可能需要至少5根K线计算MA5")
        
        # 9. 模拟执行并检查订单
        print("\n[9] 模拟策略执行...")
        
        # 创建足够的数据用于MA5计算
        bars = []
        base_time = int(datetime.now().timestamp() * 1000)
        for i in range(5):
            bar_time = base_time - (4 - i) * 86400000  # 每天一根
            price = 10.0 + i * 0.5
            bars.append({
                'open_time': bar_time,
                'close_time': bar_time + 86400000,
                'open': str(price),
                'high': str(price + 0.2),
                'low': str(price - 0.2),
                'close': str(price + 0.1),  # 价格递增
                'volume': '1000000',
            })
        
        # 计算MA5
        closes = [float(b['close']) for b in bars]
        ma5 = sum(closes) / len(closes)
        current_price = closes[-1]
        print(f"  MA5: {ma5:.2f}")
        print(f"  当前价格: {current_price:.2f}")
        print(f"  触发条件: 当前价格 > MA5 * 1.01 = {ma5 * 1.01:.2f}")
        
        if current_price > ma5 * 1.01:
            print(f"  ✓ 价格条件满足（{current_price:.2f} > {ma5 * 1.01:.2f}）")
        else:
            warnings.append(f"⚠️  价格条件不满足（{current_price:.2f} <= {ma5 * 1.01:.2f}），不会触发买入")
            print(f"  ✗ 价格条件不满足")
        
        exec_request['market_data_context'] = [{
            'symbol': '000001.XSHE',
            'timeframe': '1d',
            'bars': bars,
        }]
        
        response = engine.execute(exec_request)
        
        print(f"\n  执行状态: {response['status']} (0=成功, 1=部分成功, 2=失败)")
        order_count = len(response.get('order_op_event', []))
        print(f"  订单数量: {order_count}")
        
        if order_count == 0:
            warnings.append("⚠️  策略执行成功但没有生成订单")
            print("  ⚠️  没有生成订单")
            
            # 分析原因
            print("\n  可能的原因:")
            if len(scheduled) > 0:
                print("    1. run_daily 注册的函数需要时间匹配才会触发")
                print("    2. 当前时间可能不在触发窗口内（如 'open' 需要是开盘时间）")
            if current_price <= ma5 * 1.01:
                print("    3. 价格条件不满足（当前价格 <= MA5 * 1.01）")
            if not exec_request['account'].available_margin or sum(exec_request['account'].available_margin.values()) == 0:
                print("    4. 账户没有可用资金")
        else:
            print("  ✓ 生成了订单")
            for i, op in enumerate(response['order_op_event'], 1):
                order = op.get('order', {})
                print(f"    订单 {i}: {order.get('symbol')} {order.get('qty')} @ {order.get('limit_price')}")
        
        if 'error_message' in response and response['error_message']:
            issues.append(f"❌ 执行错误: {response['error_message']}")
            print(f"  ❌ 错误: {response['error_message']}")
        
        # 10. 总结
        print("\n" + "=" * 80)
        print("诊断总结")
        print("=" * 80)
        
        if issues:
            print("\n❌ 发现的问题:")
            for issue in issues:
                print(f"  {issue}")
        
        if warnings:
            print("\n⚠️  警告:")
            for warning in warnings:
                print(f"  {warning}")
        
        if not issues and not warnings:
            print("\n✓ 所有检查通过，策略应该可以正常工作")
        
        print("\n建议:")
        if len(scheduled) > 0:
            print("  - run_daily 注册的函数需要时间匹配，确保当前时间在触发窗口内")
        if order_count == 0 and current_price <= ma5 * 1.01:
            print("  - 调整测试数据，使当前价格 > MA5 * 1.01 才能触发买入")
        if order_count == 0 and len(scheduled) > 0:
            print("  - 考虑使用 handle_bar 而不是 run_daily，这样每次收到K线数据都会触发")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        strategy_path = sys.argv[1]
    else:
        strategy_path = "strategy/double_mean.py"
    
    diagnose_strategy(strategy_path)

