"""
WealthAI SDK 异常处理测试
"""

import unittest

from wealthai_sdk.exceptions import WealthAISDKError, NotFoundError, ParseError


class TestExceptions(unittest.TestCase):
    """异常处理测试类"""
    
    def test_wealthai_sdk_error_base(self):
        """测试基础异常类"""
        error = WealthAISDKError("测试错误")
        
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "测试错误")
    
    def test_not_found_error_basic(self):
        """测试 NotFoundError 基本功能"""
        error = NotFoundError("binance", "BTCUSDT")
        
        # 检查继承关系
        self.assertIsInstance(error, WealthAISDKError)
        self.assertIsInstance(error, Exception)
        
        # 检查属性
        self.assertEqual(error.broker, "binance")
        self.assertEqual(error.symbol, "BTCUSDT")
        self.assertEqual(error.resource_type, "resource")
        
        # 检查错误消息
        expected_message = "未找到 binance/BTCUSDT 的resource"
        self.assertEqual(str(error), expected_message)
    
    def test_not_found_error_with_resource_type(self):
        """测试带资源类型的 NotFoundError"""
        error = NotFoundError("okx", "ETHUSDT", "交易规则")
        
        self.assertEqual(error.broker, "okx")
        self.assertEqual(error.symbol, "ETHUSDT")
        self.assertEqual(error.resource_type, "交易规则")
        
        expected_message = "未找到 okx/ETHUSDT 的交易规则"
        self.assertEqual(str(error), expected_message)
    
    def test_not_found_error_different_resource_types(self):
        """测试不同资源类型的 NotFoundError"""
        test_cases = [
            ("binance", "BTCUSDT", "交易规则"),
            ("okx", "ETHUSDT", "佣金费率"),
            ("huobi", "ADAUSDT", "配置文件"),
            ("bybit", "DOGEUSDT", "数据源")
        ]
        
        for broker, symbol, resource_type in test_cases:
            error = NotFoundError(broker, symbol, resource_type)
            
            self.assertEqual(error.broker, broker)
            self.assertEqual(error.symbol, symbol)
            self.assertEqual(error.resource_type, resource_type)
            
            expected_message = f"未找到 {broker}/{symbol} 的{resource_type}"
            self.assertEqual(str(error), expected_message)
    
    def test_parse_error_basic(self):
        """测试 ParseError 基本功能"""
        file_path = "/path/to/config.json"
        error = ParseError(file_path)
        
        # 检查继承关系
        self.assertIsInstance(error, WealthAISDKError)
        self.assertIsInstance(error, Exception)
        
        # 检查属性
        self.assertEqual(error.file_path, file_path)
        self.assertEqual(error.reason, "格式错误")
        
        # 检查错误消息
        expected_message = f"解析文件 {file_path} 失败: 格式错误"
        self.assertEqual(str(error), expected_message)
    
    def test_parse_error_with_reason(self):
        """测试带原因的 ParseError"""
        file_path = "/path/to/config.json"
        reason = "JSON 格式无效"
        error = ParseError(file_path, reason)
        
        self.assertEqual(error.file_path, file_path)
        self.assertEqual(error.reason, reason)
        
        expected_message = f"解析文件 {file_path} 失败: {reason}"
        self.assertEqual(str(error), expected_message)
    
    def test_parse_error_different_reasons(self):
        """测试不同原因的 ParseError"""
        test_cases = [
            ("/config/binance.json", "JSON 语法错误"),
            ("/config/okx.json", "缺少必需字段"),
            ("/config/huobi.json", "数据类型不匹配"),
            ("/config/bybit.json", "文件编码错误")
        ]
        
        for file_path, reason in test_cases:
            error = ParseError(file_path, reason)
            
            self.assertEqual(error.file_path, file_path)
            self.assertEqual(error.reason, reason)
            
            expected_message = f"解析文件 {file_path} 失败: {reason}"
            self.assertEqual(str(error), expected_message)
    
    def test_exception_raising(self):
        """测试异常抛出和捕获"""
        # 测试 NotFoundError
        with self.assertRaises(NotFoundError) as context:
            raise NotFoundError("binance", "BTCUSDT", "交易规则")
        
        error = context.exception
        self.assertEqual(error.broker, "binance")
        self.assertEqual(error.symbol, "BTCUSDT")
        
        # 测试 ParseError
        with self.assertRaises(ParseError) as context:
            raise ParseError("/config/test.json", "测试错误")
        
        error = context.exception
        self.assertEqual(error.file_path, "/config/test.json")
        self.assertEqual(error.reason, "测试错误")
    
    def test_exception_inheritance_catching(self):
        """测试异常继承和捕获"""
        # NotFoundError 可以被 WealthAISDKError 捕获
        with self.assertRaises(WealthAISDKError):
            raise NotFoundError("binance", "BTCUSDT")
        
        # ParseError 可以被 WealthAISDKError 捕获
        with self.assertRaises(WealthAISDKError):
            raise ParseError("/config/test.json")
        
        # 都可以被 Exception 捕获
        with self.assertRaises(Exception):
            raise NotFoundError("binance", "BTCUSDT")
        
        with self.assertRaises(Exception):
            raise ParseError("/config/test.json")


if __name__ == '__main__':
    unittest.main()