# Design: 策略测试后自动打开可视化预览

## Context

当前策略测试流程：
1. 运行 `python3 test_strategy.py strategy/xxx.py`
2. 生成 JSON 数据文件
3. 手动启动 React 模板：`cd visualization/react-template && npm run dev`
4. 手动打开浏览器
5. 手动上传 JSON 文件

这个流程太繁琐，开发者需要立即看到测试结果来判断策略是否合理。

## Goals

1. **一键预览**：测试完成后自动打开浏览器预览
2. **自动加载**：无需手动上传文件，自动加载刚生成的数据
3. **框架验证可视化**：直观显示框架是否支持策略运行
4. **策略合理性分析**：帮助开发者快速判断策略逻辑

## Non-Goals

- 不实现策略代码自动修复
- 不实现策略性能分析（未来可扩展）
- 不实现策略对比功能（未来可扩展）

## Decisions

### 1. 自动预览实现方式

**决策**：使用 Python `http.server` + `webbrowser` 模块

**理由**：
- Python 标准库，无需额外依赖
- 简单可靠，跨平台支持
- 可以自动打开浏览器并传递 URL 参数
- 不依赖 React 模板是否运行

**实现方式**：
```python
import http.server
import socketserver
import webbrowser
from threading import Thread

# 启动 HTTP 服务器
PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    # 在后台线程运行
    server_thread = Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    
    # 打开浏览器
    json_url = f"http://localhost:{PORT}/{json_filename}"
    react_url = f"http://localhost:5173?data={json_url}"
    webbrowser.open(react_url)
```

### 2. React 模板启动方式

**决策**：检测 React 模板是否运行，如果没有则提示启动

**理由**：
- 避免每次都启动新的 React 服务器（占用资源）
- 如果已经运行，直接使用
- 如果没有运行，提供清晰的启动提示

**实现方式**：
```python
def check_react_server():
    try:
        response = requests.get("http://localhost:5173", timeout=1)
        return True
    except:
        return False

if not check_react_server():
    print("⚠️  React 模板未运行")
    print("   请先启动: cd visualization/react-template && npm run dev")
    # 仍然启动 HTTP 服务器，用户可以手动访问
```

### 3. 框架验证数据收集

**决策**：在数据收集器中添加框架验证结果

**数据结构**：
```python
framework_verification = {
    "g": True,
    "log": True,
    "run_daily": True,
    "order_value": True,
    "order_target": True,
    "wealthdata_api": True,
    "errors": []
}
```

### 4. 策略分析数据收集

**决策**：收集策略执行的关键信息

**数据结构**：
```python
strategy_analysis = {
    "execution_status": "success",  # success, partial, failed
    "has_orders": True,
    "order_count": 1,
    "buy_orders": 0,
    "sell_orders": 1,
    "data_validation": {
        "price_condition_met": True,
        "ma5_calculated": True,
        "timeframe_detected": True
    },
    "warnings": [],
    "errors": []
}
```

### 5. React 组件设计

**框架验证面板**：
- 显示所有框架功能的可用性
- 使用颜色标记（绿色=正常，红色=异常）
- 显示错误信息（如果有）

**策略分析面板**：
- 显示执行状态
- 显示订单统计
- 显示数据验证结果
- 显示警告和错误

## Risks / Trade-offs

### 风险 1：端口冲突

**风险**：HTTP 服务器端口 8000 可能被占用

**缓解**：
- 检测端口是否可用
- 如果被占用，尝试其他端口（8001, 8002...）
- 在 URL 中使用实际端口号

### 风险 2：React 模板未运行

**风险**：用户没有启动 React 模板

**缓解**：
- 检测 React 服务器是否运行
- 提供清晰的启动提示
- 仍然启动 HTTP 服务器，用户可以手动访问

### 风险 3：浏览器打开失败

**风险**：某些环境下无法自动打开浏览器

**缓解**：
- 打印访问 URL
- 用户可以手动复制 URL 访问

## Implementation Plan

### 阶段 1：自动预览功能
1. 修改 `test_strategy.py` 添加自动预览
2. 实现 HTTP 服务器启动
3. 实现浏览器自动打开
4. 测试不同操作系统

### 阶段 2：数据收集增强
1. 修改 `data_collector.py` 收集框架验证结果
2. 修改 `data_collector.py` 收集策略分析信息
3. 修改 `data_exporter.py` 导出新数据

### 阶段 3：React 组件开发
1. 创建 `FrameworkVerification.tsx` 组件
2. 创建 `StrategyAnalysis.tsx` 组件
3. 集成到 `App.tsx`

### 阶段 4：测试和优化
1. 端到端测试
2. 不同操作系统测试
3. 错误处理优化

