"""
WealthAI SDK 配置管理测试
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from wealthai_sdk.config import Config


class TestConfig(unittest.TestCase):
    """配置管理测试类"""
    
    def __init__(self, *args, **kwargs):
        """初始化测试类"""
        super().__init__(*args, **kwargs)
        # 初始化实例变量以满足类型检查器要求
        self.temp_dir: str = ""
        self.temp_path: Path = Path()
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': ''}, clear=True)
    @patch('wealthai_sdk.config.Path.home')
    def test_config_dir_user_home(self, mock_home):
        """测试使用用户目录作为配置目录"""
        mock_home.return_value = self.temp_path
        
        config = Config()
        
        # 应该使用用户目录/.wealthai
        expected_dir = self.temp_path / ".wealthai"
        self.assertEqual(config.config_dir, expected_dir)
        
        # 目录应该被创建
        self.assertTrue(expected_dir.exists())
    
    @patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': ''}, clear=True)
    @patch('wealthai_sdk.config.Path.__file__')
    def test_config_dir_project_config(self, mock_file):
        """测试使用项目配置目录"""
        # 模拟项目结构
        project_root = self.temp_path / "project"
        project_root.mkdir()
        config_dir = project_root / "config"
        config_dir.mkdir()
        
        # 模拟 __file__ 路径
        mock_file.return_value = str(project_root / "wealthai_sdk" / "config.py")
        
        config = Config()
        
        # 应该使用项目的 config 目录
        self.assertEqual(config.config_dir, config_dir)
    
    def test_config_dir_environment_variable(self):
        """测试使用环境变量指定配置目录"""
        custom_config_dir = self.temp_path / "custom_config"
        custom_config_dir.mkdir()
        
        with patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': str(custom_config_dir)}):
            config = Config()
            self.assertEqual(config.config_dir, custom_config_dir)
    
    def test_get_trading_rules_file(self):
        """测试获取交易规则文件路径"""
        with patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': str(self.temp_path)}):
            config = Config()
            
            binance_file = config.get_trading_rules_file("binance")
            expected_path = self.temp_path / "trading_rules" / "binance.json"
            
            self.assertEqual(binance_file, expected_path)
    
    def test_get_commission_rates_file(self):
        """测试获取佣金费率文件路径"""
        with patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': str(self.temp_path)}):
            config = Config()
            
            binance_file = config.get_commission_rates_file("binance")
            expected_path = self.temp_path / "commission_rates" / "binance.json"
            
            self.assertEqual(binance_file, expected_path)
    
    def test_multiple_brokers(self):
        """测试多个交易所的文件路径"""
        with patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': str(self.temp_path)}):
            config = Config()
            
            # 测试不同交易所
            brokers = ["binance", "okx", "huobi", "bybit"]
            
            for broker in brokers:
                trading_file = config.get_trading_rules_file(broker)
                commission_file = config.get_commission_rates_file(broker)
                
                # 检查路径格式
                self.assertTrue(trading_file.name.endswith(f"{broker}.json"))
                self.assertTrue(commission_file.name.endswith(f"{broker}.json"))
                
                # 检查父目录
                self.assertEqual(trading_file.parent.name, "trading_rules")
                self.assertEqual(commission_file.parent.name, "commission_rates")
    
    def test_config_dir_property(self):
        """测试配置目录属性访问"""
        with patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': str(self.temp_path)}):
            config = Config()
            
            # 多次访问应该返回相同的路径
            dir1 = config.config_dir
            dir2 = config.config_dir
            
            self.assertEqual(dir1, dir2)
            self.assertIsInstance(dir1, Path)
    
    @patch.dict(os.environ, {'WEALTHAI_CONFIG_DIR': '/nonexistent/path'}, clear=True)
    def test_config_dir_nonexistent_env_path(self):
        """测试环境变量指向不存在的路径"""
        config = Config()
        
        # 即使路径不存在，也应该使用环境变量的值
        expected_path = Path('/nonexistent/path')
        self.assertEqual(config.config_dir, expected_path)


if __name__ == '__main__':
    unittest.main()