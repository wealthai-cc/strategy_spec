# WebSocket 行情接入功能

## 概述

本功能实现了 WebSocket 实时行情数据接入，策略可以通过现有 API 透明地获取实时行情数据，无需修改策略代码。

## 核心特性

- ✅ **完全透明**：策略无需修改，继续使用 `wealthdata.get_price()` 等现有 API
- ✅ **混合数据源**：优先使用 WebSocket 实时数据，如果没有则使用 Context 历史数据
- ✅ **向后兼容**：回测场景自动回退到 Context 数据，完全兼容
- ✅ **自动重连**：网络断开时自动重连，保证数据连续性
- ✅ **线程安全**：支持多策略并发访问

## 架构设计

```
WebSocket 服务端
    ↓ (推送实时数据)
WebSocket 客户端 (后台服务)
    ↓ (存储到缓存)
全局数据缓存
    ↓ (数据适配器读取)
ContextDataAdapter.get_history()
    ↓ (策略调用)
wealthdata.get_price() / context.history()
```

## 文件结构

```
engine/python_sdk/
├── websocket_client.py      # WebSocket 客户端实现
├── websocket_cache.py        # 数据缓存实现
├── websocket_manager.py      # 配置和管理器
├── context_data_adapter.py   # 混合数据源适配器（已扩展）
└── exceptions.py             # 异常类型（已扩展）

tests/
├── test_websocket_cache.py           # 缓存测试
├── test_websocket_client.py          # 客户端测试
├── test_websocket_manager.py         # 管理器测试
├── test_websocket_integration.py     # 集成测试
└── test_websocket_mock.py            # Mock 测试（无需 WebSocket 库）

example_websocket_usage.py            # 使用示例
```

## 快速开始

### 1. 安装依赖

```bash
pip install websocket-client>=1.6.0
```

### 2. 系统级配置（策略管理系统）

```python
from engine.python_sdk.websocket_manager import get_websocket_manager

# 配置并启动
manager = get_websocket_manager()
manager.configure(
    symbols=["BTCUSDT", "ETHUSDT"],
    resolutions=["1m", "5m", "1h"]
)
manager.start()

# 检查状态
status = manager.get_status()
print(f"WebSocket state: {status['state']}")
```

### 3. 策略使用（无需修改）

```python
from wealthdata import get_price

def handle_bar(context, bar):
    # 自动从 WebSocket 缓存或 Context 获取数据
    df = get_price('BTCUSDT', count=20, frequency='1h')
    ma = df['close'].mean()
    # ... 策略逻辑
```

## 环境变量配置（可选）

```bash
export WEBSOCKET_ENDPOINT="wss://ws.wealthai.cc:18000/market_data"
export WEBSOCKET_CSRF_TOKEN="your_token"
export WEBSOCKET_MARKET_TYPE="binance-testnet"
export WEBSOCKET_SYMBOLS="BTCUSDT,ETHUSDT"
export WEBSOCKET_RESOLUTIONS="1m,5m,1h"
```

## 测试

### 运行测试

```bash
# 安装测试依赖
pip install pytest websocket-client

# 运行所有 WebSocket 测试
pytest tests/test_websocket_*.py -v

# 运行简单测试（无需 pytest）
python3 test_websocket_simple.py
```

### 测试覆盖

- ✅ WebSocket 缓存功能
- ✅ 数据适配器集成
- ✅ 混合数据源逻辑
- ✅ 向后兼容性
- ⚠️ WebSocket 客户端连接（需要服务端）
- ⚠️ 自动重连机制（需要服务端）

## API 文档

### WebSocketManager

系统级配置和管理接口。

```python
manager = get_websocket_manager()

# 配置
manager.configure(symbols=[...], resolutions=[...])

# 启动
manager.start()

# 停止
manager.stop()

# 更新订阅
manager.update_subscription(symbols=[...], resolutions=[...])

# 查询状态
status = manager.get_status()
```

### WebSocketCache

数据缓存接口（通常不需要直接使用）。

```python
from engine.python_sdk.websocket_cache import get_websocket_cache

cache = get_websocket_cache()

# 获取数据
bars = cache.get_bars("BTCUSDT", "1h", count=20)

# 获取最新数据
latest = cache.get_latest_bar("BTCUSDT", "1h")
```

## 故障排查

### WebSocket 连接失败

1. 检查网络连接
2. 检查端点配置是否正确
3. 检查 CSRF token 是否有效
4. 查看日志获取详细错误信息

### 数据未更新

1. 检查 WebSocket 连接状态：`manager.get_status()`
2. 检查订阅列表是否正确
3. 检查缓存中是否有数据：`cache.get_cached_symbols()`

### 回测场景问题

回测场景会自动使用 Context 数据，WebSocket 缓存为空是正常的。如果遇到问题，检查：
1. Context 中是否有 market_data_context
2. 数据适配器是否正确注册

## 性能考虑

- 缓存大小限制：每个 (symbol, timeframe) 最多 1000 根 K 线
- 线程安全：所有操作都是线程安全的
- 内存使用：缓存使用 deque，自动管理大小

## 已知限制

1. 需要安装 `websocket-client` 库
2. 端到端测试需要真实的 WebSocket 服务端
3. 数据格式需要与服务端保持一致

## 相关文档

- [实施总结](./实施总结.md)
- [测试和集成总结](./测试和集成总结.md)
- [设计文档](./design.md)
- [提案文档](./proposal.md)

## 更新日志

### 2025-01-XX
- ✅ 实现 WebSocket 客户端
- ✅ 实现数据缓存
- ✅ 扩展数据适配器
- ✅ 实现配置管理
- ✅ 编写测试用例

