"""
WealthAI SDK 异常定义
"""


class WealthAISDKError(Exception):
    """WealthAI SDK 基础异常类"""
    pass


class NotFoundError(WealthAISDKError):
    """当本地不存在对应的交易规则或佣金费率时抛出"""
    
    def __init__(self, broker: str, symbol: str, resource_type: str = "resource"):
        self.broker = broker
        self.symbol = symbol
        self.resource_type = resource_type
        super().__init__(f"未找到 {broker}/{symbol} 的{resource_type}")


class ParseError(WealthAISDKError):
    """当配置文件存在但格式错误时抛出"""
    
    def __init__(self, file_path: str, reason: str = "格式错误"):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"解析文件 {file_path} 失败: {reason}")