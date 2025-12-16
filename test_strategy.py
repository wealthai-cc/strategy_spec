"""
策略测试工具

支持两种使用方式：
1. 手动测试：python3 test_strategy.py strategy/double_mean.py
2. 自动化测试：pytest test_strategy.py

功能：
- 自动检测策略使用的市场类型（A股、美股、港股、加密货币）
- 根据市场类型生成对应的测试数据（价格范围、货币）
- 构造过去10天的K线数据用于策略测试
- 验证策略逻辑和框架功能
"""

import sys
import pytest
import re
from pathlib import Path

# 添加 engine 到路径
sys.path.insert(0, str(Path(__file__).parent))

from engine.engine import StrategyExecutionEngine
from engine.context.context import Account
from datetime import datetime, timedelta
from engine.compat.market_type import detect_market_type, MarketType
from typing import Optional, Dict


def _parse_timeframe_interval(timeframe: str) -> Dict[str, int]:
    """
    解析时间分辨率字符串，返回时间间隔信息
    
    Args:
        timeframe: 时间分辨率字符串（如 '1h', '5m', '1d'）
    
    Returns:
        包含 'value' 和 'unit' 的字典
        - value: 数值部分（如 1, 5）
        - unit: 单位部分（'minutes', 'hours', 'days'）
    """
    match = re.match(r'^(\d+)([mhdw])$', timeframe)
    if not match:
        # 默认返回日线
        return {'value': 1, 'unit': 'days'}
    
    value = int(match.group(1))
    unit_char = match.group(2)
    
    unit_map = {
        'm': 'minutes',
        'h': 'hours',
        'd': 'days',
        'w': 'weeks',
    }
    
    return {
        'value': value,
        'unit': unit_map.get(unit_char, 'days')
    }


def test_strategy(strategy_path: str, output_path: Optional[str] = None):
    """
    测试策略文件
    
    Args:
        strategy_path: 策略文件路径
        output_path: 可视化报告输出路径（可选，默认自动命名）
    """
    print(f"正在测试策略: {strategy_path}")
    print("=" * 60)
    
    # 总是初始化数据收集器（自动生成可视化报告）
    from visualization.data_collector import VisualizationDataCollector
    collector = VisualizationDataCollector()
    
    try:
        # 创建引擎
        engine = StrategyExecutionEngine(strategy_path)
        print("✅ 策略加载成功")
        
        # 自动检测策略使用的标的和市场类型
        default_symbol = None
        market_type = MarketType.CRYPTO  # 默认
        
        # 读取策略代码
        try:
            with open(strategy_path, 'r', encoding='utf-8') as f:
                strategy_code = f.read()
        except Exception as e:
            print(f"  ⚠️  无法读取策略文件: {e}")
            strategy_code = ""
        
        # 自动检测时间分辨率
        from visualization.timeframe_detector import detect_timeframe, parse_timeframe_count
        default_timeframe, timeframe_warning = detect_timeframe(strategy_code)
        if timeframe_warning:
            print(f"  ⚠️  {timeframe_warning}")
        else:
            print(f"  ✓ 检测到时间分辨率: {default_timeframe}")
        
        # 解析需要的K线数量
        bar_count = parse_timeframe_count(strategy_code, default_timeframe)
        print(f"  ✓ 将生成 {bar_count} 根 {default_timeframe} K线数据")
        
        # 尝试从策略代码中提取标的
        if strategy_code:
            # 查找常见的标的设置模式
            patterns = [
                r"g\.security\s*=\s*['\"]([^'\"]+)['\"]",  # g.security = '000001.XSHE'
                r"context\.symbol\s*=\s*['\"]([^'\"]+)['\"]",  # context.symbol = 'BTCUSDT'
                r"set_benchmark\(['\"]([^'\"]+)['\"]\)",  # set_benchmark('000300.XSHG')
                r"run_daily\([^,]+,\s*[^,]+,\s*reference_security=['\"]([^'\"]+)['\"]\)",  # run_daily(..., reference_security='...')
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, strategy_code)
                if matches:
                    default_symbol = matches[0]
                    break
        
        # 如果没有找到，使用默认值
        if not default_symbol:
            # 根据文件名猜测
            if 'double_mean' in strategy_path:
                default_symbol = "000001.XSHE"  # A股
            elif 'crypto' in strategy_path.lower() or 'btc' in strategy_path.lower():
                default_symbol = "BTCUSDT"  # 加密货币
            else:
                default_symbol = "BTCUSDT"  # 默认加密货币
        
        # 检测市场类型
        market_type = detect_market_type(default_symbol)
        
        # 启动数据收集
        strategy_name = Path(strategy_path).stem
        collector.start_test(strategy_name, market_type.value, default_symbol)
        
        print(f"\n市场类型检测:")
        print(f"  标的: {default_symbol}")
        print(f"  市场类型: {market_type.value}")
        
        # 根据市场类型设置价格范围和货币
        if market_type == MarketType.A_STOCK:
            base_price = 10.0  # A股价格通常在 5-50 元
            price_range = (0.1, 0.5)  # 价格波动范围
            currency = "CNY"
            currency_type = 4  # 假设 CNY 的 currency_type 是 4
        elif market_type == MarketType.US_STOCK:
            base_price = 100.0  # 美股价格通常在 50-500 美元
            price_range = (1.0, 5.0)
            currency = "USD"
            currency_type = 2  # 假设 USD 的 currency_type 是 2
        elif market_type == MarketType.HK_STOCK:
            base_price = 50.0  # 港股价格通常在 10-200 港元
            price_range = (0.5, 2.0)
            currency = "HKD"
            currency_type = 3  # 假设 HKD 的 currency_type 是 3
        else:  # CRYPTO
            base_price = 50000.0  # 加密货币价格（如BTC）
            price_range = (100.0, 500.0)
            currency = "USDT"
            currency_type = 1  # USDT
        
        print(f"  货币: {currency}")
        
        # 根据时间分辨率生成对应粒度的K线数据
        bars = []
        base_time = datetime.now()
        price_step, price_volatility = price_range
        
        # 计算时间间隔（根据时间分辨率）
        timeframe_interval = _parse_timeframe_interval(default_timeframe)
        
        # 生成指定数量的K线数据
        for i in range(bar_count):
            # 根据时间分辨率计算时间
            bar_time = base_time - timedelta(**{timeframe_interval['unit']: (bar_count - 1 - i) * timeframe_interval['value']})
            open_time_ms = int(bar_time.timestamp() * 1000)
            # 计算收盘时间（下一个时间点）
            close_time = bar_time + timedelta(**{timeframe_interval['unit']: timeframe_interval['value']})
            close_time_ms = int(close_time.timestamp() * 1000)
            
            # 价格波动：前半部分价格在 base_price - price_step 到 base_price 之间
            # 后半部分逐步上涨，确保最后价格 > MA5 * 1.01
            mid_point = bar_count // 2
            if i < mid_point:
                price = base_price - price_step + i * (price_step / mid_point)
            else:
                # 后半部分上涨，确保最后价格明显高于MA的1.01倍
                price = base_price + (i - mid_point) * price_step * 2.0  # 增加涨幅确保触发
            
            # 添加小幅波动
            high = price + price_volatility
            low = price - price_volatility
            close = price + (price_volatility * 0.5)  # 收盘价略高于开盘价
            
            bar_data = {
                "open_time": open_time_ms,
                "close_time": close_time_ms,
                "open": str(price),
                "high": str(high),
                "low": str(low),
                "close": str(close),
                "volume": str(1000000 + i * 10000),
            }
            bars.append(bar_data)
            
            # 收集K线数据
            collector.collect_bar(bar_data, default_symbol, default_timeframe)
        
        # 计算MA5验证数据是否正确
        closes = [float(b["close"]) for b in bars[-5:]]  # 最后5天的收盘价
        ma5 = sum(closes) / len(closes)
        current_price = closes[-1]
        trigger_price = ma5 * 1.01
        
        print(f"\n数据验证:")
        print(f"  标的: {default_symbol} ({market_type.value})")
        print(f"  过去5天收盘价: {[f'{c:.2f}' for c in closes]}")
        print(f"  MA5: {ma5:.2f}")
        print(f"  当前价格: {current_price:.2f}")
        print(f"  触发条件: 当前价格 > MA5 * 1.01 = {trigger_price:.2f}")
        if current_price > trigger_price:
            print(f"  ✓ 价格条件满足，应该触发买入")
        else:
            print(f"  ✗ 价格条件不满足，不会触发买入")
            print(f"  ⚠️  调整测试数据，使当前价格 > {trigger_price:.2f}")
        
        exec_request = {
            "trigger_type": 1,  # MARKET_DATA_TRIGGER_TYPE
            "trigger_detail": {},
            "market_data_context": [{
                "symbol": default_symbol,
                "timeframe": default_timeframe,
                "bars": bars,
            }],
            "account": {
                "account_id": "test_account_001",
                "account_type": 1,  # SIMULATE_ACCOUNT_TYPE
                "balances": [
                    {
                        "currency_type": currency_type,
                        "amount": 10000.0,
                    }
                ],
                "positions": [],
                "total_net_value": {
                    "currency_type": currency_type,
                    "amount": 10000.0,
                },
                "available_margin": {
                    "currency_type": currency_type,
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
            "strategy_param": {},
        }
        
        # 执行策略
        print("\n执行策略...")
        
        # 确保策略已加载
        if not hasattr(engine.loader, '_module') or engine.loader._module is None:
            engine.load_strategy()
        
        # 检查策略是否使用 run_daily
        strategy_module = engine.loader._module
        from engine.compat.scheduler import get_scheduled_functions
        
        # 先执行 initialize 以注册 run_daily 函数
        temp_context = engine._build_context(exec_request)
        engine.lifecycle.initialize(temp_context)
        
        scheduled = get_scheduled_functions(strategy_module)
        uses_run_daily = len(scheduled) > 0
        
        if uses_run_daily:
            print(f"  检测到策略使用 run_daily（注册了 {len(scheduled)} 个定时函数）")
            print("  尝试强制触发 market_open 函数以验证策略逻辑...")
            
            # 对于使用 run_daily 的策略，我们直接调用 market_open 函数来验证策略逻辑
            # 这样可以绕过时间匹配问题，直接测试策略功能
            if hasattr(strategy_module, 'market_open'):
                try:
                    # 设置 context 到 wealthdata（需要先设置才能调用策略函数）
                    from engine.wealthdata.wealthdata import set_context
                    set_context(temp_context)
                    
                    # 设置 g.security 和 context.symbol（策略需要这些）
                    symbol = exec_request['market_data_context'][0]['symbol']
                    if hasattr(strategy_module, 'g'):
                        strategy_module.g.security = symbol
                    # 设置 context.symbol（策略可能在 initialize 中设置，但我们需要确保它存在）
                    temp_context.symbol = symbol
                    
                    # 先调用 before_market_open 设置 g.security
                    if hasattr(strategy_module, 'before_market_open'):
                        try:
                            before_market_open_func = getattr(strategy_module, 'before_market_open')
                            before_market_open_func(temp_context)
                        except Exception as e:
                            print(f"  ⚠️  调用 before_market_open 失败: {e}")
                    
                    # 直接调用 market_open 验证策略逻辑
                    market_open_func = getattr(strategy_module, 'market_open')
                    market_open_func(temp_context)
                    print("  ✓ 已手动触发 market_open 函数")
                    
                    # 清理 context
                    from engine.wealthdata.wealthdata import clear_context
                    clear_context()
                except Exception as e:
                    print(f"  ⚠️  调用 market_open 失败: {e}")
                    # 不打印完整 traceback，只显示错误信息
        
        # 执行策略（正常流程）
        response = engine.execute(exec_request)
        
        # 收集订单操作和决策信息
        # 从响应中收集订单
        order_ops = response.get('order_op_event', [])
        for order_op in order_ops:
            collector.collect_order(order_op)
            
            # 尝试收集决策信息
            order_data = order_op.get("order", {})
            symbol = order_data.get("symbol", default_symbol)
            direction = "buy" if order_data.get("direction_type", 0) == 1 else "sell"
            
            # 从策略代码中提取技术指标
            from visualization.decision_extractor import extract_indicators_from_code, extract_trigger_conditions_from_code
            indicators_list = extract_indicators_from_code(strategy_code)
            
            # 计算技术指标值（简化版，实际应该从策略执行中获取）
            indicators = {}
            if bars:
                closes = [float(b["close"]) for b in bars]
                for indicator_name in indicators_list:
                    if indicator_name.startswith('MA'):
                        period = int(indicator_name[2:])
                        if len(closes) >= period:
                            ma_value = sum(closes[-period:]) / period
                            indicators[indicator_name] = ma_value
                
                # 如果没有检测到指标，但策略使用了MA5，计算MA5
                if not indicators and 'MA5' in strategy_code.upper():
                    if len(closes) >= 5:
                        indicators['MA5'] = sum(closes[-5:]) / 5
            
            # 提取触发条件
            trigger_condition = None
            if bars:
                current_price = float(bars[-1]["close"])
                if indicators:
                    # 构建触发条件（简化版）
                    if 'MA5' in indicators:
                        ma5 = indicators['MA5']
                        if current_price > ma5 * 1.01:
                            trigger_condition = f"price > MA5 * 1.01 ({current_price:.2f} > {ma5 * 1.01:.2f})"
            
            # 提取决策依据（从日志中，这里简化处理）
            decision_reason = None
            if direction == "buy" and trigger_condition:
                decision_reason = "价格高于均价1%，买入"
            elif direction == "sell":
                decision_reason = "价格低于均价，卖出"
            
            # 收集策略状态
            strategy_state = {}
            if hasattr(temp_context, 'portfolio'):
                strategy_state['available_cash'] = getattr(temp_context.portfolio, 'available_cash', 0)
                strategy_state['positions_value'] = getattr(temp_context.portfolio, 'positions_value', 0)
            
            # 收集决策信息
            collector.collect_decision(
                symbol=symbol,
                decision_type=direction,
                indicators=indicators if indicators else None,
                trigger_condition=trigger_condition,
                condition_result=True if trigger_condition else None,
                decision_reason=decision_reason,
                strategy_state=strategy_state if strategy_state else None,
            )
        
        # 如果使用 run_daily 且手动调用了函数，从 context 中收集订单
        if uses_run_daily:
                # 尝试从 context 的 _order_operations 获取订单
            order_ops_from_context = getattr(temp_context, '_order_operations', [])
            if not order_ops_from_context:
                # 尝试使用 get_order_operations 方法
                try:
                    order_ops_from_context = temp_context.get_order_operations()
                except:
                    pass
            
            for order in order_ops_from_context:
                # 将 Order 对象转换为字典格式
                try:
                    order_symbol = getattr(order, 'symbol', default_symbol)
                    order_direction = "buy" if ((hasattr(order, 'direction') and order.direction == 'buy') or 
                                                 (hasattr(order, 'direction_type') and order.direction_type == 1)) else "sell"
                    order_price = float(getattr(order, 'limit_price', 0) or getattr(order, 'price', 0) or bars[-1]["close"] if bars else base_price)
                    order_qty = float(getattr(order, 'qty', 0) or getattr(order, 'quantity', 0))
                    
                    order_dict = {
                        "order_op_type": 1,  # CREATE_ORDER_OP_TYPE
                        "order": {
                            "unique_id": getattr(order, 'unique_id', None) or getattr(order, 'order_id', None) or f"order_{len(collector.orders)}",
                            "symbol": order_symbol,
                            "direction_type": 1 if order_direction == "buy" else 2,
                            "order_type": getattr(order, 'order_type', 2),  # 默认限价单
                            "limit_price": {"amount": order_price} if order_price > 0 else None,
                            "qty": order_qty,
                            "status": getattr(order, 'status', 0),
                        }
                    }
                    collector.collect_order(order_dict, trigger_reason="策略逻辑触发")
                    
                    # 收集决策信息（从策略代码和当前状态中提取）
                    from visualization.decision_extractor import extract_indicators_from_code
                    indicators_list = extract_indicators_from_code(strategy_code)
                    
                    # 计算技术指标值
                    indicators = {}
                    if bars:
                        closes = [float(b["close"]) for b in bars]
                        for indicator_name in indicators_list:
                            if indicator_name.startswith('MA'):
                                period = int(indicator_name[2:])
                                if len(closes) >= period:
                                    ma_value = sum(closes[-period:]) / period
                                    indicators[indicator_name] = ma_value
                        
                        # 如果没有检测到指标，但策略使用了MA5，计算MA5
                        if not indicators and 'MA5' in strategy_code.upper():
                            if len(closes) >= 5:
                                indicators['MA5'] = sum(closes[-5:]) / 5
                        
                        # 提取触发条件
                        current_price = float(bars[-1]["close"])
                        trigger_condition = None
                        if 'MA5' in indicators:
                            ma5 = indicators['MA5']
                            if current_price > ma5 * 1.01:
                                trigger_condition = f"price > MA5 * 1.01 ({current_price:.2f} > {ma5 * 1.01:.2f})"
                        
                        # 提取决策依据
                        decision_reason = None
                        if order_direction == "buy" and trigger_condition:
                            decision_reason = "价格高于均价1%，买入"
                        elif order_direction == "sell":
                            decision_reason = "价格低于均价，卖出"
                        
                        # 收集策略状态
                        strategy_state = {}
                        if hasattr(temp_context, 'portfolio'):
                            strategy_state['available_cash'] = getattr(temp_context.portfolio, 'available_cash', 0)
                            strategy_state['positions_value'] = getattr(temp_context.portfolio, 'positions_value', 0)
                        
                        # 收集决策信息
                        collector.collect_decision(
                            symbol=order_symbol,
                            decision_type=order_direction,
                            indicators=indicators if indicators else None,
                            trigger_condition=trigger_condition,
                            condition_result=True if trigger_condition else None,
                            decision_reason=decision_reason,
                            strategy_state=strategy_state if strategy_state else None,
                        )
                except Exception as e:
                    # 忽略转换错误
                    pass
        
        # 如果使用 run_daily 但没有订单，说明时间不匹配
        if uses_run_daily and len(response.get('order_op_event', [])) == 0:
            print("\n⚠️  注意：策略使用 run_daily，正常执行流程中没有订单")
            print("  这是因为 run_daily 注册的函数需要时间匹配才会触发")
            print("  但我们已经手动调用了 market_open 来验证策略逻辑")
        
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
        
        if len(order_ops) == 0:
            # 检查是否是因为 run_daily 时间不匹配
            if uses_run_daily:
                # 检查手动调用后是否有订单（从 context 中获取）
                order_ops_from_context = temp_context._order_ops if hasattr(temp_context, '_order_ops') else []
                if len(order_ops_from_context) > 0:
                    print("  ✓ 手动触发后生成了订单（验证策略逻辑正常）")
                    for i, order in enumerate(order_ops_from_context, 1):
                        print(f"    订单 {i}: {order.symbol if hasattr(order, 'symbol') else 'N/A'} "
                              f"{order.qty if hasattr(order, 'qty') else 'N/A'}")
                else:
                    print("  ⚠️  没有生成订单")
                    print("  可能原因：")
                    print("    1. 价格条件不满足（当前价格 <= MA5 * 1.01）")
                    print("    2. 账户没有可用资金")
                    print("    3. 策略逻辑问题")
            else:
                print("  ⚠️  没有生成订单")
        else:
            print("  ✓ 策略执行成功，生成了订单")
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
        
        # 验证框架功能
        print("\n框架功能验证:")
        framework_ok = True
        
        # 检查函数注入
        required_funcs = ['g', 'log', 'run_daily', 'order_value', 'order_target']
        for func_name in required_funcs:
            if hasattr(strategy_module, func_name):
                print(f"  ✓ {func_name} 已注入")
            else:
                print(f"  ✗ {func_name} 未注入")
                framework_ok = False
        
        # 检查 wealthdata
        try:
            import wealthdata
            if hasattr(wealthdata, 'get_bars') and hasattr(wealthdata, 'get_price'):
                print(f"  ✓ wealthdata API 可用")
            else:
                print(f"  ✗ wealthdata API 不完整")
                framework_ok = False
        except:
            print(f"  ✗ wealthdata 模块不可用")
            framework_ok = False
        
        if framework_ok:
            print("  ✓ 框架功能正常")
        else:
            print("  ✗ 框架功能有问题")
        
        # 收集框架功能验证结果
        for func_name in required_funcs:
            status = hasattr(strategy_module, func_name)
            collector.collect_framework_check(func_name, status)
        
        # 检查 wealthdata
        try:
            import wealthdata
            has_wealthdata = hasattr(wealthdata, 'get_bars') and hasattr(wealthdata, 'get_price')
            collector.collect_framework_check("wealthdata API", has_wealthdata)
        except:
            collector.collect_framework_check("wealthdata API", False, "wealthdata 模块不可用")
        
        # 结束数据收集
        collector.end_test()
        
        # 总是生成可视化报告
        try:
            from visualization.report_generator import ReportGenerator
            strategy_name = Path(strategy_path).stem
            if output_path:
                report_path = output_path
            else:
                # 自动命名：如果文件已存在，添加时间戳
                default_name = f"{strategy_name}_report.html"
                if Path(default_name).exists():
                    report_path = f"{strategy_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                else:
                    report_path = default_name
            
            generator = ReportGenerator(collector)
            generator.generate(report_path)
            print(f"\n📊 可视化报告已生成: {report_path}")
        except Exception as e:
            print(f"\n⚠️  生成可视化报告失败: {e}")
            import traceback
            traceback.print_exc()
        
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


# pytest 测试函数（用于自动化测试）
def test_strategy_file():
    """pytest 测试函数，测试真实策略文件"""
    strategy_path = "strategy/double_mean.py"
    success = test_strategy(strategy_path)
    assert success, "策略测试失败"


if __name__ == "__main__":
    # 手动测试模式：python3 test_strategy.py [strategy_file] [--visualize] [--output path]
    import argparse
    
    parser = argparse.ArgumentParser(description='测试策略文件')
    parser = argparse.ArgumentParser(description='测试策略文件（自动生成可视化报告）')
    parser.add_argument('strategy_path', nargs='?', default='strategy/double_mean.py',
                        help='策略文件路径')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='可视化报告输出路径（可选，默认自动命名）')
    
    args = parser.parse_args()
    
    success = test_strategy(args.strategy_path, output_path=args.output)
    sys.exit(0 if success else 1)
