"""
数据导出模块

负责将数据收集器的数据导出为 JSON 格式，供 React 模板加载使用。
"""

import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from .data_collector import VisualizationDataCollector, BarData, OrderData, DecisionInfo, FrameworkCheck


# 数据格式版本
DATA_FORMAT_VERSION = "1.1.0"


def export_to_json(collector: VisualizationDataCollector, output_path: str) -> str:
    """
    将数据收集器的数据导出为 JSON 格式
    
    Args:
        collector: 数据收集器实例
        output_path: 输出文件路径
    
    Returns:
        输出文件的绝对路径
    """
    # 确保输出目录存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 构建数据字典
    data = {
        "version": DATA_FORMAT_VERSION,
        "metadata": _build_metadata(collector),
        "bars": _build_bars_data(collector.bars),
        "orders": _build_orders_data(collector.orders),
        "decisions": _build_decisions_data(collector.decisions),
        "statistics": _build_statistics(collector),
        "framework_verification": _build_framework_verification(collector),
        "strategy_analysis": _build_strategy_analysis(collector),
    }
    
    # 写入 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return str(output_file.absolute())


def _build_metadata(collector: VisualizationDataCollector) -> Dict[str, Any]:
    """构建元数据"""
    return {
        "strategy_name": collector.strategy_name or "unknown",
        "symbol": collector.symbol or "unknown",
        "market_type": collector.market_type or "unknown",
        "test_start_time": collector.test_start_time.isoformat() if collector.test_start_time else None,
        "test_end_time": collector.test_end_time.isoformat() if collector.test_end_time else None,
        "timeframe": _detect_timeframe(collector.bars),
    }


def _detect_timeframe(bars: list) -> str:
    """从 K 线数据中检测时间分辨率"""
    if not bars:
        return "1d"
    
    # 从第一个 bar 的 timeframe 字段获取
    if hasattr(bars[0], 'timeframe') and bars[0].timeframe:
        return bars[0].timeframe
    
    # 如果没有，尝试从时间间隔推断
    if len(bars) >= 2:
        interval_ms = bars[1].open_time - bars[0].open_time
        # 转换为常见的时间分辨率
        if interval_ms < 60000:  # < 1分钟
            return "1m"
        elif interval_ms < 3600000:  # < 1小时
            minutes = interval_ms / 60000
            return f"{int(minutes)}m"
        elif interval_ms < 86400000:  # < 1天
            hours = interval_ms / 3600000
            return f"{int(hours)}h"
        else:  # >= 1天
            days = interval_ms / 86400000
            return f"{int(days)}d"
    
    return "1d"


def _build_bars_data(bars: list) -> list:
    """构建 K 线数据，包含技术指标"""
    result = []
    all_closes = [float(bar.close) for bar in bars]
    
    # 计算技术指标（为所有K线计算）
    def calculate_ma(prices, period):
        ma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                ma_values.append(prices[i])
            else:
                ma = sum(prices[i - period + 1:i + 1]) / period
                ma_values.append(ma)
        return ma_values
    
    def calculate_ema(prices, period):
        ema_values = []
        multiplier = 2.0 / (period + 1)
        for i in range(len(prices)):
            if i == 0:
                ema_values.append(prices[i])
            elif i < period - 1:
                ema = sum(prices[:i+1]) / (i + 1)
                ema_values.append(ema)
            else:
                ema = (prices[i] - ema_values[-1]) * multiplier + ema_values[-1]
                ema_values.append(ema)
        return ema_values
    
    def calculate_bollinger_bands(prices, period=20, std_dev=2.0):
        upper_band = []
        middle_band = []
        lower_band = []
        for i in range(len(prices)):
            if i < period - 1:
                price = prices[i]
                middle_band.append(price)
                upper_band.append(price)
                lower_band.append(price)
            else:
                period_prices = prices[i - period + 1:i + 1]
                ma = sum(period_prices) / period
                middle_band.append(ma)
                variance = sum((p - ma) ** 2 for p in period_prices) / period
                std = variance ** 0.5
                upper_band.append(ma + std_dev * std)
                lower_band.append(ma - std_dev * std)
        return upper_band, middle_band, lower_band
    
    def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        dif = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]
        dea = calculate_ema(dif, signal_period)
        macd_bar = [(dif[i] - dea[i]) * 2 for i in range(len(prices))]
        return dif, dea, macd_bar
    
    def calculate_rsi(prices, period=14):
        rsi_values = []
        for i in range(len(prices)):
            if i < period:
                rsi_values.append(50.0)
            else:
                gains = []
                losses = []
                for j in range(i - period + 1, i + 1):
                    if j > 0:
                        change = prices[j] - prices[j - 1]
                        if change > 0:
                            gains.append(change)
                            losses.append(0)
                        else:
                            gains.append(0)
                            losses.append(abs(change))
                avg_gain = sum(gains) / period if gains else 0
                avg_loss = sum(losses) / period if losses else 0
                if avg_loss == 0:
                    rsi = 100.0
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        return rsi_values
    
    # 计算所有指标
    ma5_values = calculate_ma(all_closes, 5) if len(all_closes) >= 5 else []
    ma10_values = calculate_ma(all_closes, 10) if len(all_closes) >= 10 else []
    ma20_values = calculate_ma(all_closes, 20) if len(all_closes) >= 20 else []
    ma30_values = calculate_ma(all_closes, 30) if len(all_closes) >= 30 else []
    ema12_values = calculate_ema(all_closes, 12) if len(all_closes) >= 12 else []
    ema26_values = calculate_ema(all_closes, 26) if len(all_closes) >= 26 else []
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(all_closes, period=20, std_dev=2.0) if len(all_closes) >= 20 else ([], [], [])
    macd_dif, macd_dea, macd_bar = calculate_macd(all_closes, fast_period=12, slow_period=26, signal_period=9) if len(all_closes) >= 26 else ([], [], [])
    rsi_values = calculate_rsi(all_closes, period=14) if len(all_closes) >= 14 else []
    
    # 构建每个bar的数据，包含指标
    for i, bar in enumerate(bars):
        bar_data = {
            "open_time": bar.open_time,
            "close_time": bar.close_time,
            "open": str(bar.open),  # 使用字符串保证精度
            "high": str(bar.high),
            "low": str(bar.low),
            "close": str(bar.close),
            "volume": str(bar.volume),
        }
        
        # 添加技术指标数据
        indicators = {}
        if i < len(ma5_values):
            indicators["MA5"] = str(round(ma5_values[i], 2))
        if i < len(ma10_values):
            indicators["MA10"] = str(round(ma10_values[i], 2))
        if i < len(ma20_values):
            indicators["MA20"] = str(round(ma20_values[i], 2))
        if i < len(ma30_values):
            indicators["MA30"] = str(round(ma30_values[i], 2))
        if i < len(ema12_values):
            indicators["EMA12"] = str(round(ema12_values[i], 2))
        if i < len(ema26_values):
            indicators["EMA26"] = str(round(ema26_values[i], 2))
        if i < len(bb_upper):
            indicators["BB_Upper"] = str(round(bb_upper[i], 2))
            indicators["BB_Middle"] = str(round(bb_middle[i], 2))
            indicators["BB_Lower"] = str(round(bb_lower[i], 2))
        if i < len(macd_dif):
            indicators["MACD_DIF"] = str(round(macd_dif[i], 2))
            indicators["MACD_DEA"] = str(round(macd_dea[i], 2))
            indicators["MACD_Bar"] = str(round(macd_bar[i], 2))
        if i < len(rsi_values):
            indicators["RSI"] = str(round(rsi_values[i], 2))
        
        if indicators:
            bar_data["indicators"] = indicators
        
        result.append(bar_data)
    
    return result


def _build_orders_data(orders: list) -> list:
    """构建订单数据"""
    return [
        {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "direction": order.direction,
            "price": str(order.price),  # 使用字符串保证精度
            "quantity": order.quantity,
            "timestamp": order.timestamp,
            "order_type": order.order_type,
            "bar_index": order.bar_index,  # K线索引（用于回测场景）
            "status": order.status,
            "trigger_reason": order.trigger_reason,
        }
        for order in orders
    ]


def _build_decisions_data(decisions: list) -> list:
    """构建决策信息数据"""
    result = []
    for decision in decisions:
        # 处理 indicators：可能是字典或字符串
        if isinstance(decision.indicators, dict):
            indicators_dict = {k: str(v) for k, v in decision.indicators.items()}
        elif isinstance(decision.indicators, str):
            # 如果是字符串，尝试解析为字典，否则使用空字典
            try:
                import json
                indicators_dict = json.loads(decision.indicators)
                indicators_dict = {k: str(v) for k, v in indicators_dict.items()}
            except (json.JSONDecodeError, TypeError, AttributeError):
                indicators_dict = {}
        else:
            indicators_dict = {}
        
        result.append({
            "timestamp": decision.timestamp,
            "symbol": decision.symbol,
            "decision_type": decision.decision_type,
            "indicators": indicators_dict,  # 使用字符串保证精度
            "trigger_condition": decision.trigger_condition,
            "condition_result": decision.condition_result,
            "decision_reason": decision.decision_reason,
            "strategy_state": decision.strategy_state,
        })
    return result


def _build_statistics(collector: VisualizationDataCollector) -> Dict[str, Any]:
    """构建统计信息"""
    buy_orders = [o for o in collector.orders if o.direction.lower() == 'buy']
    sell_orders = [o for o in collector.orders if o.direction.lower() == 'sell']
    
    return {
        "total_orders": len(collector.orders),
        "buy_orders": len(buy_orders),
        "sell_orders": len(sell_orders),
        "total_bars": len(collector.bars),
        "total_decisions": len(collector.decisions),
    }


def _build_framework_verification(collector: VisualizationDataCollector) -> Dict[str, Any]:
    """构建框架验证数据"""
    checks = collector.framework_checks if hasattr(collector, 'framework_checks') else []
    
    return {
        "checks": [
            {
                "feature_name": check.feature_name,
                "status": check.status,
                "details": check.details,
            }
            for check in checks
        ],
        "overall_status": all(check.status for check in checks) if checks else None,
        "total_checks": len(checks),
        "passed_checks": sum(1 for check in checks if check.status),
    }


def _build_strategy_analysis(collector: VisualizationDataCollector) -> Dict[str, Any]:
    """构建策略分析数据"""
    buy_orders = [o for o in collector.orders if o.direction.lower() == 'buy']
    sell_orders = [o for o in collector.orders if o.direction.lower() == 'sell']
    
    # 判断执行状态
    execution_status = "success"
    if len(collector.orders) == 0:
        execution_status = "no_orders"
    elif len(collector.bars) == 0:
        execution_status = "no_data"
    
    # 收集错误和警告（从 function_calls 中提取）
    errors = []
    warnings = []
    if hasattr(collector, 'function_calls'):
        for call in collector.function_calls:
            if call.function_name == 'log' and call.args:
                log_message = str(call.args[0]) if call.args else ""
                if 'error' in log_message.lower() or 'exception' in log_message.lower():
                    errors.append(log_message)
                elif 'warning' in log_message.lower() or 'warn' in log_message.lower():
                    warnings.append(log_message)
    
    return {
        "execution_status": execution_status,
        "order_statistics": {
            "total": len(collector.orders),
            "buy": len(buy_orders),
            "sell": len(sell_orders),
        },
        "data_validation": {
            "has_bars": len(collector.bars) > 0,
            "has_orders": len(collector.orders) > 0,
            "has_decisions": len(collector.decisions) > 0,
            "bar_count": len(collector.bars),
        },
        "errors": errors,
        "warnings": warnings,
    }

