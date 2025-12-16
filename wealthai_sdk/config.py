"""
配置管理模块
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """SDK 配置管理"""
    
    def __init__(self):
        self._config_dir: Optional[Path] = None
        self._init_config_dir()
    
    def _init_config_dir(self):
        """初始化配置目录"""
        # 优先级：环境变量 > 项目根目录/config > 用户目录/.wealthai
        
        # 1. 检查环境变量
        env_config_dir = os.getenv("WEALTHAI_CONFIG_DIR")
        if env_config_dir:
            self._config_dir = Path(env_config_dir)
            return
        
        # 2. 检查项目根目录/config
        project_config = Path(__file__).parent.parent / "config"
        if project_config.exists():
            self._config_dir = project_config
            return
        
        # 3. 使用用户目录/.wealthai
        user_config = Path.home() / ".wealthai"
        user_config.mkdir(exist_ok=True)
        self._config_dir = user_config
    
    @property
    def config_dir(self) -> Path:
        """获取配置目录路径"""
        return self._config_dir
    
    def get_trading_rules_file(self, broker: str) -> Path:
        """获取交易规则文件路径"""
        return self.config_dir / "trading_rules" / f"{broker}.json"
    
    def get_commission_rates_file(self, broker: str) -> Path:
        """获取佣金费率文件路径"""
        return self.config_dir / "commission_rates" / f"{broker}.json"


# 全局配置实例
config = Config()