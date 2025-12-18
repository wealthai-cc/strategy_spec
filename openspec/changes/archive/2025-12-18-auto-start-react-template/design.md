# Design: 自动启动 React 模板

## Context

当前用户需要：
1. 手动启动 React 模板：`cd visualization/react-template && npm run dev`
2. 运行测试：`python3 test_strategy.py strategy/xxx.py`
3. 手动打开浏览器查看结果

用户希望：
- 只需要运行 `python3 test_strategy.py strategy/xxx.py`
- 自动启动 React 模板（如果没运行）
- 自动打开浏览器查看结果

## Goals

1. **完全自动化**：用户只需运行测试文件，所有步骤自动完成
2. **智能检测**：自动检测 React 是否运行，避免重复启动
3. **可靠启动**：确保 React 服务器在测试完成前已就绪
4. **优雅管理**：管理服务器生命周期，提供优雅的关闭机制

## Non-Goals

- 不实现 React 模板的自动构建和部署
- 不实现多实例管理（同时运行多个 React 服务器）
- 不实现服务器自动重启（如果崩溃）

## Decisions

### Decision 1: React 服务器启动方式

**What**: 使用 `subprocess.Popen` 启动 `npm run dev`，在后台运行

**Why**:
- Python 标准库，无需额外依赖
- 可以控制进程生命周期
- 可以捕获输出和错误
- 跨平台支持

**Implementation**:
```python
import subprocess
from pathlib import Path

react_template_dir = Path(__file__).parent / "react-template"
process = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=react_template_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    start_new_session=True  # 独立进程组
)
```

### Decision 2: 服务器就绪检测

**What**: 使用 HTTP 请求轮询检测服务器是否就绪

**Why**:
- 准确判断服务器是否真正可用
- 不依赖端口检测（端口占用不等于服务器可用）
- 可以处理服务器启动延迟

**Implementation**:
```python
def wait_for_server(url: str, timeout: int = 30, interval: float = 0.5):
    """等待服务器就绪"""
    import time
    import urllib.request
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except:
            time.sleep(interval)
    return False
```

### Decision 3: 进程管理策略

**What**: 跟踪进程对象，提供关闭方法，但不自动关闭

**Why**:
- 用户可能想继续使用 React 服务器
- 可以手动关闭（如果需要）
- 避免频繁启动关闭（节省时间）

**Implementation**:
```python
class ReactLauncher:
    def __init__(self):
        self.process = None
    
    def start(self):
        if self.is_running():
            return True
        
        self.process = subprocess.Popen(...)
        return wait_for_server("http://localhost:5173")
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
```

### Decision 4: 错误处理策略

**What**: 提供清晰的错误提示，但不中断测试流程

**Why**:
- 测试仍然可以完成（生成 JSON 文件）
- 用户可以手动启动 React 查看结果
- 不会因为 React 启动失败而影响测试

**Implementation**:
```python
try:
    launcher.start()
except ReactStartError as e:
    print(f"⚠️  React 服务器启动失败: {e}")
    print(f"   请手动启动: cd visualization/react-template && npm run dev")
    # 继续执行测试，生成 JSON 文件
```

## Implementation Details

### ReactLauncher 类设计

```python
class ReactLauncher:
    """React 服务器启动器"""
    
    def __init__(self, port: int = 5173, timeout: int = 30):
        self.port = port
        self.timeout = timeout
        self.process = None
        self.base_url = f"http://localhost:{port}"
    
    def is_running(self) -> bool:
        """检测服务器是否运行"""
        try:
            urllib.request.urlopen(self.base_url, timeout=1)
            return True
        except:
            return False
    
    def start(self) -> bool:
        """启动 React 服务器"""
        if self.is_running():
            return True
        
        # 启动进程
        # 等待就绪
        # 返回结果
    
    def stop(self):
        """停止 React 服务器"""
        # 终止进程
```

### 集成到 test_strategy.py

```python
def test_strategy(..., auto_preview: bool = True, auto_start_react: bool = True):
    # ... 测试逻辑 ...
    
    if auto_preview:
        # 启动 React（如果需要）
        if auto_start_react:
            from visualization.react_launcher import ReactLauncher
            launcher = ReactLauncher()
            if not launcher.start():
                print("⚠️  React 服务器启动失败，请手动启动")
        
        # 启动预览服务器
        # 打开浏览器
```

## Error Handling

### 场景 1: npm 未安装
- 检测：尝试运行 `npm --version`
- 处理：提示用户安装 Node.js 和 npm
- 降级：继续执行测试，生成 JSON 文件

### 场景 2: 端口被占用
- 检测：尝试绑定端口或检测端口占用
- 处理：提示用户关闭占用端口的进程，或使用其他端口
- 降级：继续执行测试，生成 JSON 文件

### 场景 3: 服务器启动失败
- 检测：等待超时或进程退出
- 处理：显示错误信息，提示手动启动
- 降级：继续执行测试，生成 JSON 文件

## Testing Strategy

### 单元测试
- 测试 `is_running()` 方法
- 测试 `start()` 方法（mock subprocess）
- 测试 `stop()` 方法
- 测试错误处理

### 集成测试
- 测试完整流程（启动 -> 测试 -> 预览）
- 测试服务器已运行的情况
- 测试启动失败的情况
- 测试多个测试连续运行

## Performance Considerations

- 服务器启动时间：通常 1-3 秒
- 检测间隔：0.5 秒（平衡响应速度和资源消耗）
- 超时时间：30 秒（足够启动，不会等待过久）

