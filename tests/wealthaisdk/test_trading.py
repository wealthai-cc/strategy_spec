"""
WealthAI SDK 交易功能测试
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from wealthai_sdk import (
    get_trading_rule, 
    get_commission_rates, 
    NotFoundError, 
    ParseError,
    clear_cache
)


class TestTradingFunctions(unittest.TestCase):
    """交易功能测试类"""
    
    def __init__(self, *args, **kwargs):
        """初始化测试类"""
        super().__init__(*args, **kwargs)
        # 初始化实例变量以满足类型检查器要求
        self.temp_dir: str = ""
        self.config_dir: Path = Path()
    
    def setUp(self):
        """测试前准备"""
        # 清空缓存
        clear_cache()
        
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # 创建配置子目录
        (self.config_dir / "trading_rules").mkdir()
        (self.config_dir / "commission_rates").mkdir()
        
        # 创建测试配置文件
        self._create_test_config_files()
    
    def _create_test_config_files(self):
        """创建测试配置文件"""
        # 交易规则文件
        trading_rules = {
            "BTCUSDT": {
                "symbol": "BTCUSDT",
                "min_quantity": 0.00001,
                "quantity_step": 0.00001,
                "min_price": 0.01,
                "price_tick": 0.01,
                "price_precision": 2,
                "quantity_precision": 5,
                "max_leverage": 125.0
            },
            "ETHUSDT": {
                "symbol": "ETHUSDT", 
                "min_quantity": 0.0001,
                "quantity_step": 0.0001,
                "min_price": 0.01,
                "price_tick": 0.01,
                "price_precision": 2,
                "quantity_precision": 4,
                "max_leverage": 75.0
            }
        }
        
        with open(self.config_dir / "trading_rules" / "binance.json", 'w') as f:
            json.dump(trading_rules, f)
        
        # 佣金费率文件
        commission_rates = {
            "BTCUSDT": {
                "maker_fee_rate": 0.0002,
                "taker_fee_rate": 0.0004
            },
            "ETHUSDT": {
                "maker_fee_rate": 0.0002,
                "taker_fee_rate": 0.0004
            }
        }
        
        with open(self.config_dir / "commission_rates" / "binance.json", 'w') as f:
            json.dump(commission_rates, f)
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_get_trading_rule_success(self, mock_config_dir):
        """测试成功获取交易规则"""
        mock_config_dir.return_value = self.config_dir
        
        result = get_trading_rule("binance", "BTCUSDT")
        
        expected = {
            'symbol': 'BTCUSDT',
            'min_quantity': 0.00001,
            'quantity_step': 0.00001,
            'min_price': 0.01,
            'price_tick': 0.01,
            'price_precision': 2,
            'quantity_precision': 5,
            'max_leverage': 125.0
        }
        
        self.assertEqual(result, expected)
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_get_trading_rule_multiple_symbols(self, mock_config_dir):
        """测试多个交易品种的规则查询"""
        mock_config_dir.return_value = self.config_dir
        
        # 测试 BTCUSDT
        btc_rule = get_trading_rule("binance", "BTCUSDT")
        self.assertEqual(btc_rule['symbol'], 'BTCUSDT')
        self.assertEqual(btc_rule['max_leverage'], 125.0)
        
        # 测试 ETHUSDT
        eth_rule = get_trading_rule("binance", "ETHUSDT")
        self.assertEqual(eth_rule['symbol'], 'ETHUSDT')
        self.assertEqual(eth_rule['max_leverage'], 75.0)
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_get_trading_rule_not_found_broker(self, mock_config_dir):
        """测试不存在的交易所"""
        mock_config_dir.return_value = self.config_dir
        
        with self.assertRaises(NotFoundError) as context:
            get_trading_rule("unknown_broker", "BTCUSDT")
        
        self.assertIn("unknown_broker", str(context.exception))
        self.assertIn("交易规则配置文件", str(context.exception))
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_get_trading_rule_not_found_symbol(self, mock_config_dir):
        """测试不存在的交易品种"""
        mock_config_dir.return_value = self.config_dir
        
        with self.assertRaises(NotFoundError) as context:
            get_trading_rule("binance", "UNKNOWN")
        
        self.assertIn("UNKNOWN", str(context.exception))
        self.assertIn("交易规则", str(context.exception))
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_get_commission_rates_success(self, mock_config_dir):
        """测试成功获取佣金费率"""
        mock_config_dir.return_value = self.config_dir
        
        result = get_commission_rates("binance", "BTCUSDT")
        
        expected = {
            'maker_fee_rate': 0.0002,
            'taker_fee_rate': 0.0004
        }
        
        self.assertEqual(result, expected)
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_get_commission_rates_multiple_symbols(self, mock_config_dir):
        """测试多个交易品种的费率查询"""
        mock_config_dir.return_value = self.config_dir
        
        # 测试 BTCUSDT
        btc_fees = get_commission_rates("binance", "BTCUSDT")
        self.assertEqual(btc_fees['maker_fee_rate'], 0.0002)
        
        # 测试 ETHUSDT
        eth_fees = get_commission_rates("binance", "ETHUSDT")
        self.assertEqual(eth_fees['taker_fee_rate'], 0.0004)
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_get_commission_rates_not_found(self, mock_config_dir):
        """测试不存在的佣金费率"""
        mock_config_dir.return_value = self.config_dir
        
        with self.assertRaises(NotFoundError) as context:
            get_commission_rates("binance", "UNKNOWN")
        
        self.assertIn("UNKNOWN", str(context.exception))
        self.assertIn("佣金费率", str(context.exception))
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_caching_mechanism(self, mock_config_dir):
        """测试缓存机制"""
        mock_config_dir.return_value = self.config_dir
        
        # 第一次调用 - 从文件读取
        result1 = get_trading_rule("binance", "BTCUSDT")
        
        # 第二次调用 - 从缓存获取
        result2 = get_trading_rule("binance", "BTCUSDT")
        
        # 结果应该相同
        self.assertEqual(result1, result2)
        
        # 测试不同的缓存键
        fees1 = get_commission_rates("binance", "BTCUSDT")
        fees2 = get_commission_rates("binance", "BTCUSDT")
        self.assertEqual(fees1, fees2)
    
    @patch('wealthai_sdk.config.config.config_dir')
    def test_cache_isolation(self, mock_config_dir):
        """测试缓存隔离性"""
        mock_config_dir.return_value = self.config_dir
        
        # 不同 broker+symbol 组合应该有独立的缓存
        btc_rule = get_trading_rule("binance", "BTCUSDT")
        eth_rule = get_trading_rule("binance", "ETHUSDT")
        
        # 验证缓存的独立性
        self.assertNotEqual(btc_rule['max_leverage'], eth_rule['max_leverage'])
    
    def test_clear_cache_function(self):
        """测试缓存清理功能"""
        # 这个测试不需要 mock，因为 clear_cache 是纯内存操作
        clear_cache()
        # 如果没有异常抛出，说明函数正常工作
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()