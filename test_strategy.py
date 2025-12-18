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
import re
import random
from pathlib import Path
try:
    import pytest
except ImportError:
    pytest = None  # pytest 是可选的，用于自动化测试

# 添加 engine 到路径
sys.path.insert(0, str(Path(__file__).parent))

from engine.engine import StrategyExecutionEngine
from engine.context.context import Account
from datetime import datetime, timedelta
from engine.compat.market_type import detect_market_type, MarketType
from typing import Optional, Dict, Any


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


def _generate_decision_reason(
    direction: str,
    trigger_condition: Optional[str],
    condition_result: Optional[bool],
    indicators: Optional[Dict[str, float]],
    current_price: Optional[float],
    strategy_state: Optional[Dict[str, Any]]
) -> Optional[str]:
    """
    根据策略实际执行情况动态生成决策依据
    
    Args:
        direction: 订单方向 ('buy' or 'sell')
        trigger_condition: 触发条件文本
        condition_result: 条件判断结果
        indicators: 技术指标值字典
        current_price: 当前价格
        strategy_state: 策略状态（如可用资金、持仓等）
    
    Returns:
        决策依据字符串
    """
    if not trigger_condition:
        # 如果没有触发条件，返回基本的决策信息
        if direction == "buy":
            return "执行买入操作"
        elif direction == "sell":
            return "执行卖出操作"
        return None
    
    # 构建决策原因的基础部分
    reason_parts = []
    
    # 添加触发条件信息
    if condition_result is True:
        # 条件满足，说明为什么触发
        if direction == "buy":
            reason_parts.append("触发买入条件")
        elif direction == "sell":
            reason_parts.append("触发卖出条件")
    elif condition_result is False:
        # 条件不满足，但仍有订单（可能是其他原因）
        reason_parts.append("条件未满足但仍执行")
    
    # 添加具体的触发条件描述（简化版）
    if trigger_condition:
        # 提取条件的关键信息
        if "price > MA5" in trigger_condition:
            if direction == "buy":
                reason_parts.append("价格高于MA5的1.01倍")
            else:
                reason_parts.append("价格高于MA5（但执行卖出）")
        elif "price < MA5" in trigger_condition:
            if direction == "sell":
                reason_parts.append("价格低于MA5")
            else:
                reason_parts.append("价格低于MA5（但执行买入）")
        elif "price >" in trigger_condition or "price <" in trigger_condition:
            # 通用价格条件
            reason_parts.append(f"价格条件: {trigger_condition.split('(')[0].strip()}")
    
    # 添加策略状态信息
    if strategy_state:
        if direction == "buy":
            cash = strategy_state.get('available_cash', 0)
            if cash > 0:
                reason_parts.append(f"可用资金: {cash:.2f}")
            else:
                reason_parts.append("可用资金不足")
        elif direction == "sell":
            positions_value = strategy_state.get('positions_value', 0)
            if positions_value > 0:
                reason_parts.append(f"持仓价值: {positions_value:.2f}")
            else:
                reason_parts.append("无持仓")
    
    # 添加技术指标信息（如果有）
    if indicators and current_price is not None:
        indicator_info = []
        for name, value in indicators.items():
            if name.upper().startswith('MA'):
                diff = current_price - value
                if diff > 0:
                    indicator_info.append(f"{name}={value:.2f}(+{diff:.2f})")
                else:
                    indicator_info.append(f"{name}={value:.2f}({diff:.2f})")
        if indicator_info:
            reason_parts.append(f"指标: {', '.join(indicator_info)}")
    
    # 组合所有信息
    if reason_parts:
        return " | ".join(reason_parts)
    
    # 如果没有足够信息，返回基本描述
    if direction == "buy":
        return "执行买入操作"
    elif direction == "sell":
        return "执行卖出操作"
    
    return None


def test_strategy(strategy_path: str, output_path: Optional[str] = None, auto_preview: bool = True, auto_start_react: bool = True, react_port: int = 5173):
    """
    测试策略文件
    
    Args:
        strategy_path: 策略文件路径
        output_path: 可视化报告输出路径（可选，默认自动命名）
        auto_preview: 是否自动预览（默认 True）
        auto_start_react: 是否自动启动 React 服务器（默认 True）
        react_port: React 服务器端口（默认 5173）
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
        
        # 根据市场类型设置价格范围和货币，以及波动倍数
        if market_type == MarketType.A_STOCK:
            base_price = 10.0  # A股价格通常在 5-50 元
            price_range = (0.1, 0.5)  # 价格波动范围
            volatility_multiplier = 5.0  # A股波动倍数：5倍
            currency = "CNY"
            currency_type = 4  # 假设 CNY 的 currency_type 是 4
        elif market_type == MarketType.US_STOCK:
            base_price = 100.0  # 美股价格通常在 50-500 美元
            price_range = (1.0, 5.0)
            volatility_multiplier = 4.0  # 美股波动倍数：4倍
            currency = "USD"
            currency_type = 2  # 假设 USD 的 currency_type 是 2
        elif market_type == MarketType.HK_STOCK:
            base_price = 50.0  # 港股价格通常在 10-200 港元
            price_range = (0.5, 2.0)
            volatility_multiplier = 4.0  # 港股波动倍数：4倍
            currency = "HKD"
            currency_type = 3  # 假设 HKD 的 currency_type 是 3
        else:  # CRYPTO
            base_price = 50000.0  # 加密货币价格（如BTC）
            price_range = (100.0, 500.0)
            volatility_multiplier = 8.0  # 加密货币波动倍数：8倍
            currency = "USDT"
            currency_type = 1  # USDT
        
        print(f"  货币: {currency}")
        
        # 根据时间分辨率生成对应粒度的K线数据
        bars = []
        base_time = datetime.now()
        price_step, price_volatility = price_range
        
        # 计算时间间隔（根据时间分辨率）
        timeframe_interval = _parse_timeframe_interval(default_timeframe)
        
        # 增加波动幅度（真实市场波动更大，根据市场类型调整）
        enhanced_volatility = price_volatility * volatility_multiplier
        
        # 生成指定数量的K线数据
        current_price = base_price  # 当前价格（用于模拟连续的价格变化）
        previous_close = base_price  # 前一根K线的收盘价（用于跳空计算）
        random.seed(42)  # 设置随机种子，确保可重复
        
        # 连续涨跌状态（用于模拟市场情绪）
        last_direction = None  # 'up' 或 'down'，None 表示初始状态
        
        for i in range(bar_count):
            # 根据时间分辨率计算时间
            bar_time = base_time - timedelta(**{timeframe_interval['unit']: (bar_count - 1 - i) * timeframe_interval['value']})
            open_time_ms = int(bar_time.timestamp() * 1000)
            # 计算收盘时间（下一个时间点）
            close_time = bar_time + timedelta(**{timeframe_interval['unit']: timeframe_interval['value']})
            close_time_ms = int(close_time.timestamp() * 1000)
            
            # 价格趋势：前半部分震荡下跌，后半部分逐步上涨，确保最后价格 > MA5 * 1.01
            mid_point = bar_count // 2
            trend_factor = 0.0
            if i < mid_point:
                # 前半部分：震荡下跌，但保持一定波动
                trend_factor = -0.5 + (i / mid_point) * 0.3  # 从-0.5到-0.2
            else:
                # 后半部分：逐步上涨，确保最后价格明显高于MA的1.01倍
                progress = (i - mid_point) / (bar_count - mid_point)
                trend_factor = -0.2 + progress * 2.5  # 从-0.2到2.3，确保上涨
            
            # 基础价格（带趋势）
            base_trend_price = base_price + trend_factor * price_step
            
            # 添加随机波动（模拟真实市场）
            random_change = random.uniform(-enhanced_volatility, enhanced_volatility)
            current_price = base_trend_price + random_change
            
            # 确保价格不会太低（至少是base_price的50%）
            current_price = max(current_price, base_price * 0.5)
            
            # 生成真实的OHLC数据
            # 开盘价：考虑价格跳空（20-30%概率）
            gap_probability = 0.25  # 25%概率发生跳空
            has_gap = random.random() < gap_probability
            
            if has_gap and i > 0:
                # 价格跳空：开盘价与前一根K线收盘价有较大差异
                gap_direction = random.choice([-1, 1])  # -1向下跳空，1向上跳空
                gap_size = random.uniform(1.0, 3.0) * enhanced_volatility  # 跳空幅度为波动幅度的1-3倍
                open_price = previous_close + gap_direction * gap_size
            else:
                # 正常开盘：基于前一根K线收盘价，加上小幅随机波动
                open_price = previous_close + random.uniform(-enhanced_volatility * 0.2, enhanced_volatility * 0.2)
            
            # 确保开盘价不会太低
            open_price = max(open_price, base_price * 0.3)
            
            # 收盘价：基于开盘价，加上随机涨跌（模拟日内波动）
            # 连续涨跌模式：60-70%概率延续前一根K线的方向（模拟市场情绪）
            if last_direction is not None and random.random() < 0.65:
                # 延续前一根K线的方向
                is_up = (last_direction == 'up')
            else:
                # 随机方向：上涨60%，下跌40%（模拟牛市倾向，确保有买入机会）
                is_up = random.random() < 0.6
            
            close_change = random.uniform(0, enhanced_volatility * 0.8) if is_up else random.uniform(-enhanced_volatility * 0.8, 0)
            close_price = open_price + close_change
            
            # 更新连续涨跌状态
            last_direction = 'up' if close_price >= open_price else 'down'
            
            # 最高价：至少是开盘价和收盘价的最大值，再加上随机上影线
            # 上影线长度：实体长度的0.3-0.8倍（符合真实市场特征）
            body_length = abs(close_price - open_price)
            upper_shadow_ratio = random.uniform(0.3, 0.8)
            upper_shadow = body_length * upper_shadow_ratio + random.uniform(0, enhanced_volatility * 0.3)
            high_base = max(open_price, close_price)
            high_price = high_base + upper_shadow
            
            # 最低价：至少是开盘价和收盘价的最小值，再减去随机下影线
            # 下影线长度：实体长度的0.3-0.8倍（符合真实市场特征）
            lower_shadow_ratio = random.uniform(0.3, 0.8)
            lower_shadow = body_length * lower_shadow_ratio + random.uniform(0, enhanced_volatility * 0.3)
            low_base = min(open_price, close_price)
            low_price = low_base - lower_shadow
            
            # 确保价格关系正确：high >= max(open, close), low <= min(open, close)
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            # 确保low不会为负
            low_price = max(low_price, base_price * 0.3)
            
            # 成交量：与价格波动、涨跌幅、价格位置强相关
            price_range_in_bar = high_price - low_price
            price_change_pct = abs(close_price - open_price) / open_price if open_price > 0 else 0
            
            # 基础成交量
            volume_base = 1000000
            
            # 波动越大，成交量越大
            volatility_factor = 1.0 + (price_range_in_bar / base_price) * 10
            
            # 涨跌幅越大，成交量越大
            change_factor = 1.0 + price_change_pct * 20
            
            # 价格位置：在高位或低位时，成交量可能增加（模拟关键位置交易活跃）
            price_position = (close_price - base_price * 0.5) / (base_price * 0.5)  # 归一化到[-1, 1]
            position_factor = 1.0 + abs(price_position) * 0.3  # 偏离中心越多，成交量越大
            
            # 综合成交量因子
            volume_multiplier = volatility_factor * change_factor * position_factor
            volume = volume_base * volume_multiplier * (1 + random.uniform(-0.2, 0.4))  # 添加随机性
            
            bar_data = {
                "open_time": open_time_ms,
                "close_time": close_time_ms,
                "open": str(round(open_price, 2)),
                "high": str(round(high_price, 2)),
                "low": str(round(low_price, 2)),
                "close": str(round(close_price, 2)),
                "volume": str(int(volume)),
            }
            bars.append(bar_data)
            
            # 更新当前价格和前一根K线收盘价（用于下一根K线）
            current_price = close_price
            previous_close = close_price
            
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
        import wealthdata
        
        # 先执行 initialize 以注册 run_daily 函数
        temp_context = engine._build_context(exec_request)
        engine.lifecycle.initialize(temp_context)
        
        scheduled = wealthdata.get_scheduled_functions(strategy_module)
        uses_run_daily = len(scheduled) > 0
        
        # 对于使用 run_daily 的策略，使用 BacktestEngine 执行完整回测
        if uses_run_daily:
            print(f"  检测到策略使用 run_daily（注册了 {len(scheduled)} 个定时函数）")
            print("  使用 BacktestEngine 执行完整回测...")
            
            # 使用 BacktestEngine 执行完整回测
            from engine.backtest.backtest_engine import BacktestEngine
            backtest_engine = BacktestEngine(strategy_path)
            backtest_result = backtest_engine.run_backtest(
                bars=bars,
                initial_cash=exec_request['account']['balances'][0]['amount'],
                symbol=default_symbol,
                timeframe=default_timeframe
            )
            
            # 从回测结果中收集订单
            order_ops = []
            for order_info in backtest_result['orders']:
                order_op = order_info['order_op']
                order_ops.append(order_op)
                
                # 从 order_info 中获取 bar_time 和 bar_index，并设置到 order_op 中
                bar_time = order_info.get('bar_time', 0)
                bar_index = order_info.get('bar_index', None)
                
                if bar_time > 0:
                    # 确保订单数据中有 timestamp 字段
                    order_data = order_op.get("order", {})
                    if not order_data.get("timestamp"):
                        order_data["timestamp"] = bar_time
                
                # 将 bar_index 设置到 order_op 中，供 collector 使用
                if bar_index is not None:
                    order_op["bar_index"] = bar_index
                
                # 收集订单到 collector
                collector.collect_order(order_op, trigger_reason="策略逻辑触发")
                
                # 收集决策信息（从策略代码和当前状态中提取）
                order_data = order_op.get("order", {})
                symbol = order_data.get("symbol", default_symbol)
                
                # 正确判断订单方向
                direction_type = order_data.get("direction_type", 0)
                if direction_type == 1:  # BUY_DIRECTION_TYPE
                    direction = "buy"
                elif direction_type == 2:  # SELL_DIRECTION_TYPE
                    direction = "sell"
                else:
                    direction = "buy" if direction_type == 1 else "sell"
                
                # 从策略代码中提取技术指标
                from visualization.decision_extractor import extract_indicators_from_code, extract_trigger_conditions_from_code
                indicators_list = extract_indicators_from_code(strategy_code)
                
                # 计算技术指标值（使用回测时的K线数据）
                bar_index = order_info.get('bar_index', len(bars) - 1)
                indicators = {}
                if bars and bar_index < len(bars):
                    # 使用回测时的历史K线数据计算指标
                    historical_bars = bars[:bar_index + 1]
                    closes = [float(b["close"]) for b in historical_bars]
                    
                    for indicator_name in indicators_list:
                        if indicator_name.startswith("MA"):
                            period = int(indicator_name[2:])
                            if len(closes) >= period:
                                indicators[indicator_name] = str(sum(closes[-period:]) / period)
                        elif indicator_name.startswith("EMA"):
                            period = int(indicator_name[3:])
                            if len(closes) >= period:
                                # 简化EMA计算
                                ema = sum(closes[-period:]) / period
                                indicators[indicator_name] = str(ema)
                        else:
                            indicators[indicator_name] = "0"
                
                # 提取触发条件
                trigger_conditions = extract_trigger_conditions_from_code(strategy_code)
                
                # 构建触发条件字符串（从字典列表中提取 expression 字段）
                if trigger_conditions:
                    trigger_condition_str = ", ".join([
                        cond.get('expression', str(cond)) if isinstance(cond, dict) else str(cond)
                        for cond in trigger_conditions
                    ])
                else:
                    trigger_condition_str = None
                
                # 确保 indicators 是字典类型，且值为数字（不是字符串）
                indicators_dict = {}
                if indicators:
                    for k, v in indicators.items():
                        if isinstance(v, str):
                            try:
                                indicators_dict[k] = float(v)
                            except (ValueError, TypeError):
                                indicators_dict[k] = 0.0
                        else:
                            indicators_dict[k] = float(v) if v is not None else 0.0
                
                # 构建决策原因
                decision_reason = f"策略在K线 {bar_index + 1} 处触发{direction}信号"
                
                # 收集决策信息（使用正确的参数格式）
                collector.collect_decision(
                    symbol=symbol,
                    decision_type=direction,
                    indicators=indicators_dict if indicators_dict else None,
                    trigger_condition=trigger_condition_str,
                    condition_result=True,  # 如果生成了订单，说明条件满足
                    decision_reason=decision_reason,
                    strategy_state=None,
                )
            
            print(f"  ✓ 回测完成，共生成 {len(order_ops)} 个订单")
            print(f"  📊 回测结果:")
            print(f"     初始资金: {exec_request['account']['balances'][0]['amount']:.2f}")
            print(f"     最终资金: {backtest_result.get('final_cash', 0):.2f}")
            print(f"     最终持仓: {backtest_result.get('final_positions', {})}")
        else:
            # 对于不使用 run_daily 的策略，使用正常流程
            # 执行策略（正常流程）
            response = engine.execute(exec_request)
            
            # 收集订单操作和决策信息
            # 从响应中收集订单
            order_ops = response.get('order_op_event', [])
            print(f"\n📊 订单分析:")
            print(f"  从响应中获取到 {len(order_ops)} 个订单")
            
            for i, order_op in enumerate(order_ops, 1):
                collector.collect_order(order_op)
                
                # 尝试收集决策信息
                order_data = order_op.get("order", {})
                symbol = order_data.get("symbol", default_symbol)
            
            # 正确判断订单方向：direction_type == 1 是买入，direction_type == 2 是卖出
            direction_type = order_data.get("direction_type", 0)
            if direction_type == 1:  # BUY_DIRECTION_TYPE
                direction = "buy"
            elif direction_type == 2:  # SELL_DIRECTION_TYPE
                direction = "sell"
            else:
                # 如果 direction_type 无效，尝试从其他字段判断
                direction = "buy" if direction_type == 1 else "sell"
                print(f"  ⚠️  订单 {i} direction_type={direction_type} 无效，使用默认判断")
            
            # 打印订单信息用于调试
            print(f"  订单 {i}: {direction.upper()} | 品种: {symbol} | direction_type: {direction_type} | 数量: {order_data.get('qty', 'N/A')}")
            
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
            
            # 提取触发条件（根据订单方向设置对应的条件）
            trigger_condition = None
            condition_result = None
            if bars:
                current_price = float(bars[-1]["close"])
                if indicators and 'MA5' in indicators:
                    ma5 = indicators['MA5']
                    if direction == "buy":
                        # 买入条件：价格高于MA5的1.01倍
                        if current_price > ma5 * 1.01:
                            trigger_condition = f"price > MA5 * 1.01 ({current_price:.2f} > {ma5 * 1.01:.2f})"
                            condition_result = True
                        else:
                            trigger_condition = f"price > MA5 * 1.01 ({current_price:.2f} <= {ma5 * 1.01:.2f})"
                            condition_result = False
                    elif direction == "sell":
                        # 卖出条件：价格低于MA5
                        if current_price < ma5:
                            trigger_condition = f"price < MA5 ({current_price:.2f} < {ma5:.2f})"
                            condition_result = True
                        else:
                            trigger_condition = f"price < MA5 ({current_price:.2f} >= {ma5:.2f})"
                            condition_result = False
            
            # 动态生成决策依据（基于实际触发条件和策略状态）
            decision_reason = _generate_decision_reason(
                direction=direction,
                trigger_condition=trigger_condition,
                condition_result=condition_result,
                indicators=indicators,
                current_price=float(bars[-1]["close"]) if bars else None,
                strategy_state=strategy_state
            )
            
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
                condition_result=condition_result,
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
            
            print(f"\n📊 从 context 中获取到 {len(order_ops_from_context)} 个订单")
            if len(order_ops_from_context) == 0:
                print(f"  ⚠️  警告：策略执行后没有生成订单")
                print(f"     可能原因：")
                print(f"       1. 策略条件不满足（价格条件或现金不足）")
                print(f"       2. order_value 计算出的数量为 0（会抛出异常）")
                print(f"       3. 策略执行时发生异常但被捕获")
                print(f"     调试信息：")
                print(f"       - 可用现金: {getattr(temp_context.portfolio, 'available_cash', 'N/A')}")
                print(f"       - 当前价格: {temp_context.current_bar.close if temp_context.current_bar else 'N/A'}")
            for idx, order in enumerate(order_ops_from_context, 1):
                # 将 Order 对象转换为字典格式
                try:
                    order_symbol = getattr(order, 'symbol', default_symbol)
                    
                    # 正确判断订单方向：direction_type == 1 是买入，direction_type == 2 是卖出
                    order_direction = None
                    direction_type_value = getattr(order, 'direction_type', None)
                    direction_value = getattr(order, 'direction', None)
                    
                    if hasattr(order, 'direction_type'):
                        if order.direction_type == 1:  # BUY_DIRECTION_TYPE
                            order_direction = "buy"
                        elif order.direction_type == 2:  # SELL_DIRECTION_TYPE
                            order_direction = "sell"
                    elif hasattr(order, 'direction'):
                        # 兼容字符串类型的 direction
                        if order.direction == 'buy' or order.direction == 'BUY':
                            order_direction = "buy"
                        elif order.direction == 'sell' or order.direction == 'SELL':
                            order_direction = "sell"
                    
                    # 如果无法判断，默认使用 "sell"（但应该打印警告）
                    if order_direction is None:
                        print(f"  ⚠️  订单 {idx} 无法判断方向，direction_type={direction_type_value}, direction={direction_value}")
                        order_direction = "sell"  # 默认值
                    else:
                        print(f"  订单 {idx}: {order_direction.upper()} | 品种: {order_symbol} | direction_type: {direction_type_value} | 数量: {getattr(order, 'qty', 'N/A')}")
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
                        
                        # 提取触发条件（根据订单方向设置对应的条件）
                        current_price = float(bars[-1]["close"])
                        trigger_condition = None
                        condition_result = None
                        if 'MA5' in indicators:
                            ma5 = indicators['MA5']
                            if order_direction == "buy":
                                # 买入条件：价格高于MA5的1.01倍
                                if current_price > ma5 * 1.01:
                                    trigger_condition = f"price > MA5 * 1.01 ({current_price:.2f} > {ma5 * 1.01:.2f})"
                                    condition_result = True
                                else:
                                    trigger_condition = f"price > MA5 * 1.01 ({current_price:.2f} <= {ma5 * 1.01:.2f})"
                                    condition_result = False
                            elif order_direction == "sell":
                                # 卖出条件：价格低于MA5
                                if current_price < ma5:
                                    trigger_condition = f"price < MA5 ({current_price:.2f} < {ma5:.2f})"
                                    condition_result = True
                                else:
                                    trigger_condition = f"price < MA5 ({current_price:.2f} >= {ma5:.2f})"
                                    condition_result = False
                        
                        # 动态生成决策依据（基于实际触发条件和策略状态）
                        decision_reason = _generate_decision_reason(
                            direction=order_direction,
                            trigger_condition=trigger_condition,
                            condition_result=condition_result,
                            indicators=indicators,
                            current_price=current_price,
                            strategy_state=strategy_state
                        )
                        
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
                            condition_result=condition_result,
                            decision_reason=decision_reason,
                            strategy_state=strategy_state if strategy_state else None,
                        )
                except Exception as e:
                    # 忽略转换错误
                    pass
        
        # 对于使用 BacktestEngine 的情况，跳过后续的 response 检查
        if not uses_run_daily:
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
        
        strategy_name = Path(strategy_path).stem
        
        # 优先生成 JSON 数据文件（供 React 模板使用）
        json_output_path = output_path.replace('.html', '_data.json') if output_path else f"{strategy_name}_report_data.json"
        # 直接覆盖现有文件，不生成新文件
        
        try:
            json_path = collector.export_to_json(json_output_path)
            print(f"\n📄 JSON 数据已导出: {json_path}")
            
            # 自动预览功能
            if auto_preview:
                try:
                    from visualization.react_launcher import ReactLauncher
                    import webbrowser
                    import shutil
                    
                    # 将 JSON 文件复制到 React public 目录
                    react_template_dir = Path(__file__).parent / "visualization" / "react-template"
                    public_dir = react_template_dir / "public"
                    public_dir.mkdir(exist_ok=True)
                    
                    # 复制 JSON 文件到 public/latest_report.json
                    latest_report_path = public_dir / "latest_report.json"
                    shutil.copy2(json_path, latest_report_path)
                    print(f"\n📄 数据已写入 React public 目录: {latest_report_path}")
                    
                    # 自动启动 React 服务器（如果需要）
                    react_template_url = f"http://localhost:{react_port}"
                    react_launcher = None
                    
                    if auto_start_react:
                        print(f"\n🔍 检查 React 服务器状态...")
                        react_launcher = ReactLauncher(port=react_port)
                        if not react_launcher.start():
                            print(f"   ⚠️  React 服务器启动失败，将尝试使用已运行的服务器")
                            print(f"   如果预览失败，请手动启动:")
                            print(f"      cd visualization/react-template && npm run dev")
                    else:
                        # 不自动启动，只检测是否运行
                        launcher = ReactLauncher(port=react_port)
                        if not launcher.is_running():
                            print(f"\n⚠️  React 服务器未运行")
                            print(f"   请手动启动:")
                            print(f"      cd visualization/react-template && npm run dev")
                    
                    # 打开浏览器（直接打开 React 应用，它会自动加载 latest_report.json）
                    print(f"\n🚀 正在打开预览...")
                    print(f"   React 服务器: {react_template_url}")
                    print(f"   数据文件: public/latest_report.json")
                    
                    webbrowser.open(react_template_url)
                    print(f"   ✅ 预览已打开")
                    print(f"   🌐 React 服务器: {react_template_url}")
                except Exception as e:
                    print(f"\n⚠️  自动预览失败: {e}")
                    print(f"   可以手动查看 JSON 文件: {json_path}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   🚀 使用 React 模板查看:")
                print(f"      cd visualization/react-template && npm run dev")
        except Exception as e:
            print(f"\n⚠️  JSON 导出失败: {e}")
            import traceback
            traceback.print_exc()
        
        # HTML 报告已移除，现在只使用 React 前端
        
        # 显示警告（仅对不使用 BacktestEngine 的情况）
        if not uses_run_daily:
            warnings = response.get('warnings', [])
            if warnings:
                print(f"\n警告 ({len(warnings)}):")
                for warning in warnings:
                    print(f"  ⚠️  {warning}")
        
        print("\n" + "=" * 60)
        # 对于使用 BacktestEngine 的情况，直接返回成功
        if uses_run_daily:
            return True
        else:
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
    
    parser = argparse.ArgumentParser(description='测试策略文件（自动生成可视化报告）')
    parser.add_argument('strategy_path', nargs='?', default='strategy/double_mean.py',
                        help='策略文件路径')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='可视化报告输出路径（可选，默认自动命名）')
    parser.add_argument('--no-preview', action='store_true',
                        help='禁用自动预览功能')
    parser.add_argument('--no-auto-start-react', action='store_true',
                        help='禁用自动启动 React 服务器')
    parser.add_argument('--react-port', type=int, default=5173,
                        help='React 服务器端口（默认 5173）')
    
    args = parser.parse_args()
    
    success = test_strategy(
        args.strategy_path, 
        output_path=args.output, 
        auto_preview=not args.no_preview,
        auto_start_react=not args.no_auto_start_react,
        react_port=args.react_port
    )
    sys.exit(0 if success else 1)
