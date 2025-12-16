"""
数据转换工具
"""

from typing import List, Any
import pandas as pd


def bars_to_dataframe(bars: List[Any]) -> pd.DataFrame:
    """
    将 Bar 对象列表转换为 pandas DataFrame
    
    Args:
        bars: Bar 对象列表，每个 Bar 对象应包含：
              - open: 开盘价
              - high: 最高价  
              - low: 最低价
              - close: 收盘价
              - volume: 成交量
              - close_time: 收盘时间戳
    
    Returns:
        pandas DataFrame，包含以下列：
        - open: 开盘价（float）
        - high: 最高价（float）
        - low: 最低价（float）
        - close: 收盘价（float）
        - volume: 成交量（float）
        
        DataFrame 索引为 close_time（Bar 的收盘时间戳）
    
    Example:
        >>> from engine.wealthdata import bars_to_dataframe
        >>> bars = context.history('BTCUSDT', 20, '1h')
        >>> df = bars_to_dataframe(bars)
        >>> ma = df['close'].mean()  # 使用 pandas 计算均值
    """
    if not bars:
        # 返回空的 DataFrame，但包含正确的列结构
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    # 提取数据
    data = []
    indices = []
    
    for bar in bars:
        # 支持字典和对象两种格式
        if hasattr(bar, '__dict__'):
            # 对象格式
            row_data = {
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume)
            }
            indices.append(bar.close_time)
        elif isinstance(bar, dict):
            # 字典格式
            row_data = {
                'open': float(bar['open']),
                'high': float(bar['high']),
                'low': float(bar['low']),
                'close': float(bar['close']),
                'volume': float(bar['volume'])
            }
            indices.append(bar['close_time'])
        else:
            raise ValueError(f"不支持的 Bar 对象类型: {type(bar)}")
        
        data.append(row_data)
    
    # 创建 DataFrame
    df = pd.DataFrame(data, index=indices)
    df.index.name = 'close_time'
    
    return df