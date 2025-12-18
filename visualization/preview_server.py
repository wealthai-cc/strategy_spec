"""
预览服务器模块

提供简单的 HTTP 服务器，用于在本地提供 JSON 数据文件访问。
"""

import http.server
import socketserver
import socket
from threading import Thread
from pathlib import Path
from typing import Optional


class PreviewServer:
    """预览服务器"""
    
    def __init__(self, port: int = 8000, base_dir: Optional[Path] = None):
        """
        初始化预览服务器
        
        Args:
            port: 服务器端口（默认 8000）
            base_dir: 服务器根目录（默认当前目录）
        """
        self.port = port
        self.base_dir = base_dir or Path.cwd()
        self.server: Optional[socketserver.TCPServer] = None
        self.server_thread: Optional[Thread] = None
    
    def find_available_port(self, start_port: int = 8000, max_attempts: int = 10) -> int:
        """
        查找可用端口
        
        Args:
            start_port: 起始端口
            max_attempts: 最大尝试次数
        
        Returns:
            可用端口号
        """
        for port in range(start_port, start_port + max_attempts):
            if self._is_port_available(port):
                return port
        raise RuntimeError(f"无法找到可用端口（尝试范围: {start_port}-{start_port + max_attempts - 1}）")
    
    def _is_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
    
    def start(self) -> int:
        """
        启动 HTTP 服务器
        
        Returns:
            实际使用的端口号
        """
        # 查找可用端口
        actual_port = self.find_available_port(self.port)
        
        # 创建自定义请求处理器，设置工作目录
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(self.base_dir), **kwargs)
        
        # 绑定 base_dir 到处理器
        CustomHTTPRequestHandler.base_dir = self.base_dir
        
        # 创建服务器
        self.server = socketserver.TCPServer(("", actual_port), CustomHTTPRequestHandler)
        self.server.allow_reuse_address = True
        
        # 在后台线程运行（使用非 daemon thread，确保服务器在测试完成后继续运行）
        self.server_thread = Thread(target=self.server.serve_forever, daemon=False)
        self.server_thread.start()
        
        return actual_port
    
    def stop(self):
        """停止 HTTP 服务器"""
        if self.server:
            self.server.shutdown()
            self.server = None
            self.server_thread = None
    
    def get_url(self, filename: str, port: Optional[int] = None) -> str:
        """
        获取文件的访问 URL
        
        Args:
            filename: 文件名
            port: 端口号（如果为 None，使用实际端口）
        
        Returns:
            文件访问 URL
        """
        actual_port = port or self.port
        # 确保文件名是相对于 base_dir 的
        if Path(filename).is_absolute():
            filename = Path(filename).relative_to(self.base_dir)
        return f"http://localhost:{actual_port}/{filename}"

