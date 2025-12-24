# WebSocket 行情接入 - 变更日志

## [未发布] - 2025-01-XX

### 新增功能

#### WebSocket 行情数据接入
- ✅ 新增 WebSocket 客户端 (`engine/python_sdk/websocket_client.py`)
  - 支持连接到 WealthAI WebSocket 行情服务
  - 自动发送 CONNECT 消息进行订阅
  - 接收并解析实时行情数据
  - 自动重连机制（最多 3 次，指数退避）
  - 连接状态管理

- ✅ 新增数据缓存 (`engine/python_sdk/websocket_cache.py`)
  - 线程安全的数据缓存
  - 按 (symbol, timeframe) 组织数据
  - 缓存大小限制（最多 1000 根 K 线）
  - 支持并发读写

- ✅ 新增 WebSocket 管理器 (`engine/python_sdk/websocket_manager.py`)
  - 系统级配置和管理接口
  - 支持环境变量配置
  - 动态订阅管理
  - 连接状态查询

- ✅ 扩展数据适配器 (`engine/python_sdk/context_data_adapter.py`)
  - 混合数据源支持
  - WebSocket 缓存优先策略
  - Context 数据回退
  - 数据合并逻辑

- ✅ 扩展异常类型 (`engine/python_sdk/exceptions.py`)
  - `WebSocketConnectionError`
  - `WebSocketSubscriptionError`

### 测试

- ✅ 新增 36 个测试用例
  - 缓存功能测试 (6 个)
  - 客户端测试 (11 个)
  - 管理器测试 (12 个)
  - 集成测试 (7 个)
- ✅ 所有测试通过 (100%)

### 文档

- ✅ 新增 17 个文档文件
  - 提案和设计文档
  - 规范变更文档
  - 使用和集成指南
  - 测试文档
  - 总结和报告

### 依赖

- ✅ 更新 `requirements.txt`
  - 添加 `websocket-client>=1.6.0`

### 行为变更

- **向后兼容**: 策略代码无需修改，完全透明
- **可选功能**: WebSocket 连接失败时自动回退到 Context 数据
- **数据优先级**: WebSocket 实时数据优先，Context 历史数据补充

### 已知问题

- 端到端测试需要真实 WebSocket 服务端（待集成阶段）
- 自动重连测试需要真实连接（待集成阶段）

### 迁移指南

无需迁移，功能完全向后兼容。策略代码无需任何修改。

### 使用方式

```python
# 系统级配置
from engine.python_sdk.websocket_manager import get_websocket_manager

manager = get_websocket_manager()
manager.configure(symbols=["BTCUSDT"], resolutions=["1m", "5m"])
manager.start()

# 策略使用（无需修改）
from wealthdata import get_price

def handle_bar(context, bar):
    df = get_price('BTCUSDT', count=20, frequency='1h')
    # 自动从 WebSocket 缓存或 Context 获取数据
```

