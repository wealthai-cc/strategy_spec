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
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class ReactLauncher:
    """React 服务器启动器"""
    
    def __init__(self, port: int = 5173, timeout: int = 60, interval: float = 0.5):
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
    
    def _detect_actual_port(self) -> Optional[int]:
        """
        从 stdout 输出中检测 Vite 实际使用的端口
        
        Returns:
            实际端口号，如果无法检测则返回 None
        """
        if not hasattr(self, '_stdout_path') or not Path(self._stdout_path).exists():
            return None
        
        try:
            # 刷新 stdout 文件
            if hasattr(self, '_stdout_file') and self._stdout_file:
                self._stdout_file.flush()
            
            # 读取 stdout 内容
            with open(self._stdout_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 查找 "Local: http://localhost:PORT/" 模式
            import re
            match = re.search(r'Local:\s+http://localhost:(\d+)/', content)
            if match:
                return int(match.group(1))
            
            # 也检查是否有端口切换提示
            if 'Port' in content and 'is in use' in content:
                # 查找新端口
                match = re.search(r'trying another one[^\n]*\n[^\n]*localhost:(\d+)', content)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        
        return None
    
    def is_running(self) -> bool:
        """
        检测 React 服务器是否运行
        
        Returns:
            True 如果服务器运行，False 否则
        """
        # 先检测实际端口（如果 stdout 可用）
        actual_port = self._detect_actual_port()
        if actual_port and actual_port != self.port:
            # 更新端口和 URL
            self.port = actual_port
            self.base_url = f"http://localhost:{actual_port}"
        
        # #region agent log
        try:
            log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
            log_path.parent.mkdir(exist_ok=True)
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "react_launcher.py:is_running",
                "message": "检查服务器状态",
                "data": {"base_url": self.base_url, "port": self.port},
                "timestamp": int(time.time() * 1000)
            }
            with open(log_path, "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        
        try:
            # 尝试连接服务器，检查是否返回有效响应
            response = urllib.request.urlopen(self.base_url, timeout=2)
            status_code = response.getcode()
            
            # #region agent log
            try:
                log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                log_path.parent.mkdir(exist_ok=True)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "react_launcher.py:is_running",
                    "message": "HTTP 响应",
                    "data": {"status_code": status_code, "url": self.base_url},
                    "timestamp": int(time.time() * 1000)
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
            
            # 检查状态码
            if status_code == 200:
                return True
            return False
        except urllib.error.URLError as e:
            # #region agent log
            try:
                log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                log_path.parent.mkdir(exist_ok=True)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "react_launcher.py:is_running",
                    "message": "连接失败",
                    "data": {"error": str(e), "url": self.base_url},
                    "timestamp": int(time.time() * 1000)
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
            # 连接被拒绝或超时
            return False
        except Exception as e:
            # #region agent log
            try:
                log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                log_path.parent.mkdir(exist_ok=True)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "react_launcher.py:is_running",
                    "message": "异常",
                    "data": {"error": str(e), "url": self.base_url},
                    "timestamp": int(time.time() * 1000)
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
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
            # 检查进程是否还在运行
            if self.process:
                poll_result = self.process.poll()
                
                # #region agent log
                try:
                    log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                    log_path.parent.mkdir(exist_ok=True)
                    
                    # 检查 stderr 文件内容（使用 'r+' 模式，确保能读取最新内容）
                    stderr_content = ""
                    if hasattr(self, '_stderr_path') and Path(self._stderr_path).exists():
                        try:
                            # 先刷新文件（如果有打开的文件句柄）
                            if hasattr(self, '_stderr_file') and self._stderr_file:
                                self._stderr_file.flush()
                            # 读取文件内容
                            with open(self._stderr_path, 'r', encoding='utf-8', errors='ignore') as f:
                                stderr_content = f.read()
                        except Exception as e:
                            stderr_content = f"读取错误: {e}"
                    
                    # 检查端口是否被占用
                    port_in_use = False
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            result = s.connect_ex(('127.0.0.1', self.port))
                            port_in_use = (result == 0)
                    except:
                        pass
                    
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A,B,D",
                        "location": "react_launcher.py:_wait_for_server",
                        "message": "等待循环",
                        "data": {
                            "elapsed": time.time() - start_time,
                            "poll_result": poll_result,
                            "port_in_use": port_in_use,
                            "stderr_length": len(stderr_content),
                            "stderr_last_50": stderr_content[-50:] if stderr_content else ""
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open(log_path, "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except:
                    pass
                # #endregion
                
                if poll_result is not None:
                    # 进程已退出，启动失败
                    if show_progress:
                        print(f"   ❌ React 服务器进程已退出（退出码: {poll_result}）")
                        # 尝试读取错误信息
                        try:
                            if hasattr(self, '_stderr_path') and Path(self._stderr_path).exists():
                                with open(self._stderr_path, 'r') as f:
                                    stderr_output = f.read()
                                if stderr_output:
                                    print(f"   错误信息:")
                                    error_lines = stderr_output.strip().split('\n')[-5:]
                                    for line in error_lines:
                                        if line.strip():
                                            print(f"      {line}")
                        except:
                            pass
                    return False
            
            # 检查服务器是否就绪
            # 增加二次确认，避免误判（服务器可能刚启动但还没完全就绪）
            is_running_result = self.is_running()
            
            # #region agent log
            try:
                log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                log_path.parent.mkdir(exist_ok=True)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C,D",
                    "location": "react_launcher.py:_wait_for_server",
                    "message": "is_running 检查",
                    "data": {
                        "elapsed": time.time() - start_time,
                        "is_running": is_running_result,
                        "attempt": attempt
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
            
            if is_running_result:
                # 短暂等待后再次确认
                time.sleep(0.3)
                is_running_confirm = self.is_running()
                
                # #region agent log
                try:
                    log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                    log_path.parent.mkdir(exist_ok=True)
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "C,D",
                        "location": "react_launcher.py:_wait_for_server",
                        "message": "二次确认",
                        "data": {
                            "elapsed": time.time() - start_time,
                            "is_running_confirm": is_running_confirm
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open(log_path, "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except:
                    pass
                # #endregion
                
                if is_running_confirm:
                    if show_progress:
                        print(f"   ✅ React 服务器已就绪（耗时 {time.time() - start_time:.1f} 秒）")
                    return True
            
            attempt += 1
            if show_progress and attempt % 4 == 0:  # 每 2 秒显示一次
                elapsed = time.time() - start_time
                # 显示进程状态
                process_status = "运行中"
                if self.process:
                    poll_result = self.process.poll()
                    if poll_result is not None:
                        process_status = f"已退出(退出码:{poll_result})"
                
                # #region agent log
                try:
                    # 检查实际端口占用情况
                    actual_port_check = False
                    for check_port in [5173, 5174, 5175, 3000, 8080]:
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                result = s.connect_ex(('127.0.0.1', check_port))
                                if result == 0:
                                    actual_port_check = True
                                    break
                        except:
                            pass
                    
                    log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                    log_path.parent.mkdir(exist_ok=True)
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "react_launcher.py:_wait_for_server",
                        "message": "进度更新",
                        "data": {
                            "elapsed": elapsed,
                            "process_status": process_status,
                            "expected_port": self.port,
                            "any_port_in_use": actual_port_check
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open(log_path, "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except:
                    pass
                # #endregion
                
                print(f"   ⏳ 等待 React 服务器启动... ({elapsed:.1f}s/{self.timeout}s) [进程:{process_status}]")
            
            time.sleep(self.interval)
        
        if show_progress:
            print(f"   ⚠️  等待超时（{self.timeout} 秒），服务器可能未正常启动")
            # 检查进程状态
            if self.process:
                poll_result = self.process.poll()
                if poll_result is None:
                    print(f"   ℹ️  进程仍在运行，但服务器未响应")
                    print(f"      可能原因：端口被占用、启动时间过长、或配置问题")
                    # 尝试读取 stderr 看看有没有错误
                    try:
                        if hasattr(self, '_stderr_path') and Path(self._stderr_path).exists():
                            with open(self._stderr_path, 'r') as f:
                                stderr_output = f.read()
                            if stderr_output:
                                print(f"   进程输出（最后几行）:")
                                error_lines = stderr_output.strip().split('\n')[-5:]
                                for line in error_lines:
                                    if line.strip():
                                        print(f"      {line}")
                    except:
                        pass
                else:
                    print(f"   ℹ️  进程已退出（退出码: {poll_result}）")
                    # 读取错误信息
                    try:
                        if self.process.stderr:
                            stderr_output = self.process.stderr.read().decode('utf-8', errors='ignore')
                            if stderr_output:
                                print(f"   错误信息:")
                                error_lines = stderr_output.strip().split('\n')[-10:]
                                for line in error_lines:
                                    if line.strip():
                                        print(f"      {line}")
                    except:
                        pass
            else:
                print(f"   ℹ️  进程对象不存在，可能启动失败")
            
            # 提供诊断建议
            print(f"   💡 诊断步骤:")
            print(f"      1. 检查端口占用: lsof -i :{self.port}")
            print(f"      2. 手动启动测试: cd {self.react_template_dir} && npm run dev")
            print(f"      3. 检查依赖: cd {self.react_template_dir} && npm install")
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
            
            # 使用文件重定向输出，避免阻塞但可以查看错误
            # 注意：Vite 启动很快（通常 < 1 秒），但首次启动可能需要编译
            import tempfile
            stderr_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')
            stderr_path = stderr_file.name
            stderr_file.close()
            
            # #region agent log
            try:
                log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                log_path.parent.mkdir(exist_ok=True)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A,E",
                    "location": "react_launcher.py:start",
                    "message": "准备启动进程",
                    "data": {
                        "port": self.port,
                        "env_port": env.get("PORT"),
                        "cwd": str(self.react_template_dir),
                        "stderr_path": stderr_path
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception as e:
                print(f"DEBUG: 日志写入失败: {e}")
            # #endregion
            
            # #region agent log
            try:
                log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                log_path.parent.mkdir(exist_ok=True)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A,B",
                    "location": "react_launcher.py:start",
                    "message": "启动进程前",
                    "data": {
                        "port": self.port,
                        "env_port": env.get("PORT"),
                        "cwd": str(self.react_template_dir),
                        "stderr_path": stderr_path
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
            
            # 使用 buffering=1 (line buffered) 确保错误及时写入
            # 同时捕获 stdout 以检测 Vite 实际使用的端口
            stdout_path = stderr_path.replace('.log', '_stdout.log')
            stdout_file = open(stdout_path, 'w', buffering=1)
            stderr_file = open(stderr_path, 'w', buffering=1)
            self.process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.react_template_dir,
                stdout=stdout_file,  # 捕获 stdout 以检测端口
                stderr=stderr_file,  # 写入文件，可以后续读取
                start_new_session=True,  # 独立进程组，避免被 Ctrl+C 终止
                env=env
            )
            # 不立即关闭文件，让进程继续写入
            self._stderr_file = stderr_file
            self._stdout_file = stdout_file
            self._stdout_path = stdout_path
            self._stderr_path = stderr_path  # 保存路径用于后续读取
            
            # #region agent log
            try:
                log_path = Path("/Users/spencerjin/Documents/wealthai_strategy_spec/.cursor/debug.log")
                log_path.parent.mkdir(exist_ok=True)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "react_launcher.py:start",
                    "message": "进程启动后",
                    "data": {
                        "pid": self.process.pid,
                        "poll": self.process.poll(),
                        "stderr_path": stderr_path
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception as e:
                print(f"DEBUG: 日志写入失败: {e}")
            # #endregion
            
            # 等待服务器就绪
            if self._wait_for_server(show_progress):
                return True
            else:
                # 启动失败，检查进程状态和错误输出
                if self.process:
                    # 检查进程是否还在运行
                    poll_result = self.process.poll()
                    if poll_result is not None:
                        # 进程已退出，读取错误信息
                        try:
                            stderr_output = ""
                            if hasattr(self, '_stderr_path') and Path(self._stderr_path).exists():
                                with open(self._stderr_path, 'r') as f:
                                    stderr_output = f.read()
                            if stderr_output and show_progress:
                                print(f"   ❌ React 服务器启动失败（退出码: {poll_result}）")
                                print(f"   错误信息:")
                                # 显示最后几行错误信息
                                error_lines = stderr_output.strip().split('\n')[-10:]
                                for line in error_lines:
                                    if line.strip():
                                        print(f"      {line}")
                        except:
                            pass
                    
                    # 清理进程
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=5)
                    except:
                        try:
                            self.process.kill()
                        except:
                            pass
                    self.process = None
                
                if show_progress:
                    print(f"   💡 诊断建议:")
                    print(f"      1. 检查端口 {self.port} 是否被占用: lsof -i :{self.port}")
                    print(f"      2. 手动启动服务器: cd {self.react_template_dir} && npm run dev")
                    print(f"      3. 检查 npm 和 Node.js 版本: npm --version && node --version")
                
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

