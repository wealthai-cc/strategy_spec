"""
时间分辨率检测模块

从策略代码中自动检测使用的时间分辨率。
"""

import re
from typing import Optional


def detect_timeframe(strategy_code: str) -> tuple[str, Optional[str]]:
    """
    从策略代码中检测时间分辨率
    
    Args:
        strategy_code: 策略代码字符串
    
    Returns:
        (timeframe, warning_message) 元组
        - timeframe: 检测到的时间分辨率（如 '1h', '1d'），如果检测不到则返回 '1d'
        - warning_message: 警告信息（如果检测失败），否则为 None
    """
    # 检测模式：按优先级排序
    patterns = [
        # get_bars(symbol, count=5, unit='1h')
        (r"get_bars\([^,]+,\s*[^,]+,\s*unit=['\"]([^'\"]+)['\"]", "unit"),
        # get_bars(symbol, count=5, frequency='1h')
        (r"get_bars\([^,]+,\s*[^,]+,\s*frequency=['\"]([^'\"]+)['\"]", "frequency"),
        # get_bars(symbol, count=5, unit='1h', fields=['close'])
        (r"get_bars\([^,]+,\s*[^,]+,\s*unit=['\"]([^'\"]+)['\"]", "unit"),
        # get_price(symbol, count=5, frequency='1h')
        (r"get_price\([^,]+,\s*[^,]+,\s*frequency=['\"]([^'\"]+)['\"]", "frequency"),
        # get_bars(symbol, count=5, unit='1h', ...) 带其他参数
        (r"get_bars\([^)]*unit=['\"]([^'\"]+)['\"]", "unit"),
        # get_bars(symbol, count=5, frequency='1h', ...) 带其他参数
        (r"get_bars\([^)]*frequency=['\"]([^'\"]+)['\"]", "frequency"),
    ]
    
    for pattern, param_name in patterns:
        match = re.search(pattern, strategy_code)
        if match:
            timeframe = match.group(1)
            # 验证时间分辨率格式
            if _is_valid_timeframe(timeframe):
                return timeframe, None
    
    # 检测失败，返回默认值
    return "1d", "无法从策略代码中检测时间分辨率，使用默认值 '1d'（日线）"


def _is_valid_timeframe(timeframe: str) -> bool:
    """
    验证时间分辨率格式是否有效
    
    Args:
        timeframe: 时间分辨率字符串（如 '1h', '5m', '1d'）
    
    Returns:
        True 如果格式有效，False 否则
    """
    # 支持的时间分辨率格式：数字 + 单位
    # 单位：m (分钟), h (小时), d (天), w (周)
    pattern = r'^\d+[mhdw]$'
    return bool(re.match(pattern, timeframe))


def parse_timeframe_count(strategy_code: str, timeframe: str) -> int:
    """
    从策略代码中解析该时间分辨率需要的K线数量
    
    Args:
        strategy_code: 策略代码字符串
        timeframe: 时间分辨率
    
    Returns:
        K线数量，如果解析不到则返回默认值
    """
    # 查找使用该时间分辨率的 get_bars 调用
    patterns = [
        rf"get_bars\([^,]+,\s*count=(\d+),\s*unit=['\"]{re.escape(timeframe)}['\"]",
        rf"get_bars\([^,]+,\s*count=(\d+),\s*frequency=['\"]{re.escape(timeframe)}['\"]",
        rf"get_bars\([^,]+,\s*count=(\d+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, strategy_code)
        if match:
            try:
                count = int(match.group(1))
                # 返回一个合理的数量（至少是 count 的 2 倍，确保有足够的数据）
                # 但至少生成 200 根K线，以便有足够的数据进行回测和可视化
                return max(count * 2, 200)
            except ValueError:
                pass
    
    # 默认返回 200 根K线（之前是20，现在改为200以提供更充足的数据）
    return 200



