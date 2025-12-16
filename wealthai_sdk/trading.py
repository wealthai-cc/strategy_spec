"""
交易相关接口实现
"""

import json
import threading
from typing import Dict, Any
from pathlib import Path

from .config import config
from .exceptions import NotFoundError, ParseError


class TradingDataCache:
    """线程安全的交易数据缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Any:
        """获取缓存数据"""
        with self._lock:
            return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存数据"""
        with self._lock:
            self._cache[key] = value
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()


# 全局缓存实例
_cache = TradingDataCache()


def _load_json_file(file_path: Path) -> Dict[str, Any]:
    """加载 JSON 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise NotFoundError("", "", f"配置文件 {file_path}")
    except json.JSONDecodeError as e:
        raise ParseError(str(file_path), f"JSON 格式错误: {e}")
    except Exception as e:
        raise ParseError(str(file_path), f"读取文件失败: {e}")


def get_trading_rule(broker: str, symbol: str) -> Dict[str, Any]:
    """
    查询指定 broker + symbol 的交易规则
    
    Args:
        broker: 交易所/券商标识，如 'binance'、'okx'
        symbol: 交易品种标识，如 'BTCUSDT'、'ETHUSDT'
    
    Returns:
        包含交易规则的字典：
        - symbol: 品种代号
        - min_quantity: 最小下单量
        - quantity_step: 数量步进
        - min_price: 最小价格
        - price_tick: 价格最小变动单位
        - price_precision: 价格精度（小数位数）
        - quantity_precision: 数量精度（小数位数）
        - max_leverage: 最大杠杆倍数
    
    Raises:
        NotFoundError: 本地无对应描述
        ParseError: 描述文件存在但解析失败
    """
    cache_key = f"trading_rule:{broker}:{symbol}"
    
    # 尝试从缓存获取
    cached_result = _cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # 加载配置文件
    config_file = config.get_trading_rules_file(broker)
    if not config_file.exists():
        raise NotFoundError(broker, symbol, "交易规则配置文件")
    
    try:
        data = _load_json_file(config_file)
    except (NotFoundError, ParseError):
        raise NotFoundError(broker, symbol, "交易规则")
    
    # 查找指定 symbol 的规则
    if symbol not in data:
        raise NotFoundError(broker, symbol, "交易规则")
    
    rule_data = data[symbol]
    
    # 验证必需字段
    required_fields = [
        'symbol', 'min_quantity', 'quantity_step', 'min_price', 
        'price_tick', 'price_precision', 'quantity_precision'
    ]
    
    for field in required_fields:
        if field not in rule_data:
            raise ParseError(str(config_file), f"缺少必需字段: {field}")
    
    # 设置默认值
    result = {
        'symbol': rule_data['symbol'],
        'min_quantity': float(rule_data['min_quantity']),
        'quantity_step': float(rule_data['quantity_step']),
        'min_price': float(rule_data['min_price']),
        'price_tick': float(rule_data['price_tick']),
        'price_precision': int(rule_data['price_precision']),
        'quantity_precision': int(rule_data['quantity_precision']),
        'max_leverage': float(rule_data.get('max_leverage', 1.0))
    }
    
    # 缓存结果
    _cache.set(cache_key, result)
    
    return result


def get_commission_rates(broker: str, symbol: str) -> Dict[str, float]:
    """
    查询指定 broker + symbol 的 Maker/Taker 佣金费率
    
    Args:
        broker: 交易所/券商标识，如 'binance'、'okx'
        symbol: 交易品种标识，如 'BTCUSDT'、'ETHUSDT'
    
    Returns:
        包含佣金费率的字典：
        - maker_fee_rate: Maker 手续费率（小数）
        - taker_fee_rate: Taker 手续费率（小数）
    
    Raises:
        NotFoundError: 本地无对应描述
        ParseError: 描述文件存在但解析失败
    """
    cache_key = f"commission_rates:{broker}:{symbol}"
    
    # 尝试从缓存获取
    cached_result = _cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # 加载配置文件
    config_file = config.get_commission_rates_file(broker)
    if not config_file.exists():
        raise NotFoundError(broker, symbol, "佣金费率配置文件")
    
    try:
        data = _load_json_file(config_file)
    except (NotFoundError, ParseError):
        raise NotFoundError(broker, symbol, "佣金费率")
    
    # 查找指定 symbol 的费率
    if symbol not in data:
        raise NotFoundError(broker, symbol, "佣金费率")
    
    rate_data = data[symbol]
    
    # 验证必需字段
    required_fields = ['maker_fee_rate', 'taker_fee_rate']
    
    for field in required_fields:
        if field not in rate_data:
            raise ParseError(str(config_file), f"缺少必需字段: {field}")
    
    result = {
        'maker_fee_rate': float(rate_data['maker_fee_rate']),
        'taker_fee_rate': float(rate_data['taker_fee_rate'])
    }
    
    # 缓存结果
    _cache.set(cache_key, result)
    
    return result


def clear_cache() -> None:
    """清空所有缓存数据"""
    _cache.clear_cache()