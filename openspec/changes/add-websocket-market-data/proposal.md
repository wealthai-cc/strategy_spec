# Change: 添加 WebSocket 行情数据接入

## Why

当前策略执行引擎通过 `ExecRequest.market_data_context` 接收行情数据，这种方式适合回测和批量数据处理场景。但对于实时交易场景，策略需要能够获取最新的实时行情数据，而不仅限于 ExecRequest 中传递的历史数据。

通过 WebSocket 接入实时行情数据，策略可以：
1. **获取最新行情**：策略在执行过程中可以获取 WebSocket 实时推送的最新 K 线数据
2. **数据源扩展**：在 ExecRequest 数据的基础上，补充实时行情数据
3. **降低延迟**：WebSocket 推送模式比轮询方式延迟更低
4. **透明集成**：策略无需改变现有代码，继续使用 `wealthdata.get_price()` 等现有 API

## What Changes

- **新增 WebSocket 后台服务**：在 Python SDK 中实现 WebSocket 客户端，作为后台服务运行，连接到 WealthAI 行情服务并接收实时数据
- **新增数据缓存机制**：WebSocket 接收的数据存储到全局缓存中，按交易对和周期组织
- **扩展数据适配器**：数据适配器优先从 WebSocket 缓存获取数据，如果没有则从 ExecRequest 的 Context 获取（混合数据源）
- **策略无需改变**：策略继续使用现有的 `wealthdata.get_price()`、`context.history()` 等 API，无需感知 WebSocket 的存在

## Impact

- **Affected specs**: 
  - `market-data` - 添加实时行情数据获取能力
  - `python-sdk` - 添加 WebSocket 订阅接口
- **Affected code**: 
  - `engine/python_sdk/websocket_client.py` - 新增 WebSocket 客户端实现（后台服务）
  - `engine/python_sdk/websocket_cache.py` - 新增 WebSocket 数据缓存管理
  - `engine/python_sdk/context_data_adapter.py` - 修改为混合数据源适配器（优先从 WebSocket 缓存读取）
  - `engine/python_sdk/wealthdata/websocket_manager.py` - 新增 WebSocket 订阅管理接口（可选，供系统配置使用）
- **Breaking changes**: 无
- **Migration**: 现有策略无需修改，新功能为可选使用

