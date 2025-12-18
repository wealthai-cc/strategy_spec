"""
React 服务器启动器模块

负责自动启动和管理 React 开发服务器。
"""

import subprocess
import time
import urllib.request
import socket
import os
import sys
from pathlib import Path
from typing import Optional


class ReactLauncher:
    """React 服务器启动器"""
    
    def __init__(self, port: int = 5173, timeout: int = 30, interval: float = 0.5):
        """
        初始化 React 启动器
        
        Args:
            port: React 服务器端口（默认 5173）
            timeout: 等待服务器启动的超时时间（秒，默认 30）
            interval: 轮询检测间隔（秒，默认 0.5）
        """
        self.port = port
        self.timeout = timeout
        self.interval = interval
        self.process: Optional[subprocess.Popen] = None
        self.base_url = f"http://localhost:{port}"
        self.react_template_dir = Path(__file__).parent / "react-template"
    
    def is_running(self) -> bool:
        """
        检测 React 服务器是否运行
        
        Returns:
            True 如果服务器运行，False 否则
        """
        try:
            urllib.request.urlopen(self.base_url, timeout=1)
            return True
        except Exception:
            return False
    
    def _check_npm_available(self) -> bool:
        """
        检查 npm 是否可用
        
        Returns:
            True 如果 npm 可用，False 否则
        """
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_port_available(self) -> bool:
        """
        检查端口是否可用
        
        Returns:
            True 如果端口可用，False 否则
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', self.port))
                # 如果连接成功，说明端口被占用（可能是 React 服务器）
                return result != 0
        except Exception:
            return False
    
    def _wait_for_server(self, show_progress: bool = True) -> bool:
        """
        等待服务器就绪
        
        Args:
            show_progress: 是否显示进度提示
        
        Returns:
            True 如果服务器就绪，False 如果超时
        """
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < self.timeout:
            if self.is_running():
                if show_progress:
                    print(f"   ✅ React 服务器已就绪（耗时 {time.time() - start_time:.1f} 秒）")
                return True
            
            attempt += 1
            if show_progress and attempt % 4 == 0:  # 每 2 秒显示一次
                elapsed = time.time() - start_time
                print(f"   ⏳ 等待 React 服务器启动... ({elapsed:.1f}s/{self.timeout}s)")
            
            time.sleep(self.interval)
        
        if show_progress:
            print(f"   ⚠️  等待超时（{self.timeout} 秒），服务器可能未正常启动")
        return False
    
    def start(self, show_progress: bool = True) -> bool:
        """
        启动 React 服务器
        
        Args:
            show_progress: 是否显示进度提示
        
        Returns:
            True 如果启动成功，False 否则
        """
        # 检查是否已运行
        if self.is_running():
            if show_progress:
                print(f"   ℹ️  React 服务器已在运行（端口 {self.port}）")
            return True
        
        # 检查 npm 是否可用
        if not self._check_npm_available():
            if show_progress:
                print(f"   ❌ npm 未安装或不可用")
                print(f"   请安装 Node.js 和 npm: https://nodejs.org/")
            return False
        
        # 检查 React 模板目录是否存在
        if not self.react_template_dir.exists():
            if show_progress:
                print(f"   ❌ React 模板目录不存在: {self.react_template_dir}")
            return False
        
        # 检查 package.json 是否存在
        package_json = self.react_template_dir / "package.json"
        if not package_json.exists():
            if show_progress:
                print(f"   ❌ package.json 不存在: {package_json}")
            return False
        
        # 检查 node_modules 是否存在（如果没有，需要先运行 npm install）
        node_modules = self.react_template_dir / "node_modules"
        if not node_modules.exists():
            if show_progress:
                print(f"   ⚠️  node_modules 不存在，需要先运行 npm install")
                print(f"   正在安装依赖（这可能需要几分钟）...")
            
            try:
                # 显示安装进度
                install_result = subprocess.run(
                    ["npm", "install"],
                    cwd=self.react_template_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # 合并输出
                    timeout=300,  # 增加超时时间到 5 分钟
                    text=True
                )
                if install_result.returncode != 0:
                    if show_progress:
                        print(f"   ❌ npm install 失败")
                        print(f"   错误输出:")
                        # 显示最后几行错误信息
                        error_lines = install_result.stdout.split('\n')[-10:]
                        for line in error_lines:
                            if line.strip():
                                print(f"      {line}")
                        print(f"   请手动运行: cd {self.react_template_dir} && npm install")
                    return False
                if show_progress:
                    print(f"   ✅ 依赖安装完成")
            except subprocess.TimeoutExpired:
                if show_progress:
                    print(f"   ❌ npm install 超时（超过 5 分钟）")
                    print(f"   请手动运行: cd {self.react_template_dir} && npm install")
                return False
            except Exception as e:
                if show_progress:
                    print(f"   ❌ npm install 失败: {e}")
                    print(f"   请手动运行: cd {self.react_template_dir} && npm install")
                return False
        
        # 启动 React 服务器
        if show_progress:
            print(f"   🚀 正在启动 React 服务器（端口 {self.port}）...")
        
        try:
            # 使用 subprocess.Popen 在后台启动
            # 设置环境变量 PORT（Vite 默认使用环境变量 PORT）
            env = os.environ.copy()
            env["PORT"] = str(self.port)
            
            self.process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.react_template_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # 独立进程组，避免被 Ctrl+C 终止
                env=env
            )
            
            # 等待服务器就绪
            if self._wait_for_server(show_progress):
                return True
            else:
                # 启动失败，清理进程
                if self.process:
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=5)
                    except:
                        try:
                            self.process.kill()
                        except:
                            pass
                    self.process = None
                return False
                
        except Exception as e:
            if show_progress:
                print(f"   ❌ 启动 React 服务器失败: {e}")
            if self.process:
                try:
                    self.process.terminate()
                except:
                    pass
                self.process = None
            return False
    
    def stop(self):
        """停止 React 服务器"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    self.process.kill()
                except:
                    pass
            except Exception:
                pass
            finally:
                self.process = None
    
    def get_url(self) -> str:
        """
        获取 React 服务器 URL
        
        Returns:
            React 服务器 URL
        """
        return self.base_url

