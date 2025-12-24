# WebSocket 行情接入设计文档

## Context

根据 PRD 文档 `PRD/websocket接入.md`，WealthAI 提供了 WebSocket 行情服务，端点信息如下：
- 外网端点：`wss://ws.wealthai.cc:18000/market_data`
- 备用端口：`18001`、`18002`

WebSocket 连接后需要先发送 CONNECT 消息进行订阅，然后才能接收行情推送。

## Goals / Non-Goals

### Goals

1. **封装 WebSocket 协议细节**：策略无需了解 CONNECT 消息格式、心跳等底层细节
2. **提供简洁的订阅接口**：策略只需指定交易对和 K 线周期即可订阅
3. **自动重连机制**：网络断开时自动重连，保证数据连续性
4. **线程安全**：支持多策略并发订阅
5. **与现有架构兼容**：不影响现有的 ExecRequest 数据传递方式

### Non-Goals

1. **不实现策略执行引擎的实时触发**：本提案仅提供数据获取能力，不涉及策略执行流程的改变
2. **不实现行情数据持久化**：数据仅保存在内存中，不持久化到数据库
3. **不实现行情数据聚合**：不提供跨多个 WebSocket 连接的数据聚合功能

## Decisions

### Decision 1: WebSocket 客户端实现位置

**决策**：在 `engine/python_sdk/` 下创建独立的 WebSocket 客户端模块

**理由**：
- 保持 SDK 模块的独立性
- 便于测试和维护
- 不影响策略执行引擎核心逻辑

**替代方案**：
- 在策略执行引擎中实现：会增加引擎复杂度，不符合关注点分离原则

### Decision 2: 数据访问方式

**决策**：WebSocket 作为后台服务，策略通过现有 API 透明访问数据

**架构设计**：
1. WebSocket 客户端在后台运行，接收实时数据并存储到全局缓存
2. 策略继续使用现有的 `wealthdata.get_price()`、`context.history()` 等 API
3. 数据适配器优先从 WebSocket 缓存读取数据，如果没有则从 Context 读取

**数据流**：
```
WebSocket 服务端
    ↓ (推送实时数据)
WebSocket 客户端 (后台服务)
    ↓ (存储到缓存)
全局数据缓存 (按 symbol + timeframe 组织)
    ↓ (数据适配器读取)
ContextDataAdapter.get_history()
    ↓ (策略调用)
wealthdata.get_price() / context.history()
```

**理由**：
- **策略无需改变**：策略继续使用现有 API，完全透明
- **向后兼容**：回测场景仍然从 Context 读取，不受影响
- **数据源优先级**：实时数据优先，历史数据作为补充
- **架构清晰**：WebSocket 是数据源，不是策略接口

**替代方案**：
- 回调函数式：策略需要处理回调，增加复杂度，不符合现有架构
- 独立 WebSocketDataAdapter：需要策略显式切换适配器，不够透明

### Decision 3: 数据适配器集成

**决策**：扩展 `ContextDataAdapter` 为混合数据源适配器，优先从 WebSocket 缓存读取，如果没有则从 Context 读取

**实现方式**：
```python
class ContextDataAdapter(DataAdapter):
    def get_history(self, symbol: str, count: int, timeframe: str) -> List[Any]:
        # 1. 优先从 WebSocket 缓存获取
        websocket_bars = websocket_cache.get_bars(symbol, count, timeframe)
        if websocket_bars:
            return websocket_bars
        
        # 2. 如果没有，从 Context 获取（回测场景）
        return self._extract_bars_from_context(symbol, count, timeframe)
```

**理由**：
- **透明切换**：策略无需感知数据来源，自动使用最佳数据源
- **向后兼容**：回测场景没有 WebSocket 数据时，自动回退到 Context
- **实时优先**：实时数据优先，保证策略获取最新行情
- **无需修改策略**：现有策略代码无需任何改动

**替代方案**：
- 创建独立的 `WebSocketDataAdapter`：需要策略或引擎显式选择适配器，不够透明
- 直接修改 `ContextDataAdapter`：实际上就是采用这种方式，但需要保证不影响回测场景

### Decision 4: WebSocket 连接和订阅管理

**决策**：使用单例模式管理 WebSocket 连接，系统级配置订阅列表

**连接管理**：
- WebSocket 客户端作为全局单例，在 SDK 初始化时启动
- 支持多策略共享同一个连接，减少资源消耗
- 订阅列表由系统配置或策略管理系统指定，策略无需关心

**订阅配置方式**：
1. **系统配置**：通过配置文件或环境变量指定需要订阅的交易对和周期
2. **策略管理系统**：策略管理系统在启动策略时，根据策略需求配置订阅
3. **动态订阅**（可选）：提供 API 供系统动态添加/移除订阅

**理由**：
- **策略无需关心**：策略不需要知道订阅细节，只需使用数据
- **统一管理**：系统统一管理订阅，避免重复和冲突
- **资源高效**：共享连接，减少资源消耗

**替代方案**：
- 策略主动订阅：策略需要调用订阅 API，增加复杂度
- 每个策略独立连接：资源消耗大，但隔离性更好（未来可考虑作为选项）

### Decision 5: 错误处理和重连

**决策**：实现自动重连机制，连接断开时自动重连，最多重试 3 次

**理由**：
- 保证数据连续性
- 减少策略需要处理的异常情况
- 符合生产环境要求

**替代方案**：
- 不自动重连：策略需要手动处理，增加复杂度

## Risks / Trade-offs

### Risk 1: WebSocket 连接稳定性

**风险**：网络不稳定可能导致频繁断开重连，影响数据接收

**缓解措施**：
- 实现指数退避重连策略
- 记录连接状态，策略可以查询连接状态
- 提供连接状态回调，策略可以感知连接问题

### Risk 2: 数据顺序和完整性

**风险**：网络延迟可能导致数据乱序或丢失

**缓解措施**：
- 在数据包中添加序列号（如果服务端支持）
- 记录最后接收的时间戳，检测数据缺失
- 提供数据完整性检查接口

### Risk 3: 性能影响

**风险**：WebSocket 连接和数据处理可能影响策略执行性能

**缓解措施**：
- 使用异步 I/O（如 `websockets` 库）
- 数据处理在独立线程中进行
- 提供性能监控接口

### Trade-off: 实时性 vs 可靠性

**权衡**：追求实时性可能导致数据丢失，追求可靠性可能增加延迟

**选择**：优先保证可靠性，在数据完整性基础上追求实时性

## Migration Plan

### Phase 1: 基础实现
1. 实现 WebSocket 客户端
2. 实现 CONNECT 消息发送和确认
3. 实现行情数据接收和解析

### Phase 2: 接口封装
1. 实现订阅接口
2. 实现回调机制
3. 集成到 DataAdapter

### Phase 3: 完善功能
1. 实现自动重连
2. 实现错误处理
3. 添加连接状态查询接口

### Phase 4: 测试和文档
1. 编写单元测试
2. 编写集成测试
3. 更新文档和示例

## 数据交互流程

### 策略执行时的数据获取流程

1. **策略调用数据 API**：
   ```python
   # 策略代码（无需改变）
   from wealthdata import get_price
   df = get_price('BTCUSDT', count=20, frequency='1h')
   ```

2. **SDK 方法获取适配器**：
   ```python
   # wealthdata.get_price() 内部
   adapter = get_data_adapter()  # 获取 ContextDataAdapter
   bars = adapter.get_history('BTCUSDT', 20, '1h')
   ```

3. **适配器混合数据源**：
   ```python
   # ContextDataAdapter.get_history() 内部
   # 1. 优先从 WebSocket 缓存获取
   bars = websocket_cache.get_bars('BTCUSDT', 20, '1h')
   if bars:
       return bars
   
   # 2. 如果没有，从 Context 获取（回测场景）
   return self._extract_bars_from_context('BTCUSDT', 20, '1h')
   ```

4. **WebSocket 后台服务**：
   - WebSocket 客户端持续接收数据
   - 数据存储到全局缓存 `websocket_cache`
   - 缓存按 `(symbol, timeframe)` 组织，保存最近 N 根 K 线

### WebSocket 服务启动

WebSocket 客户端在以下时机启动：
1. **SDK 初始化时**：如果配置了 WebSocket 端点，自动启动
2. **策略管理系统启动策略时**：根据策略需求启动并配置订阅
3. **手动启动**（可选）：提供 API 供系统手动启动

## Open Questions

1. **数据格式**：WebSocket 推送的数据格式是什么？是否与 `market_data.proto` 中定义的格式一致？
2. **心跳机制**：是否需要实现心跳机制？服务端是否要求心跳？
3. **订阅配置**：订阅列表如何配置？通过配置文件、环境变量还是策略管理系统？
4. **数据缓存大小**：缓存最近多少根 K 线？建议 1000 根，但需要根据内存情况调整
5. **缓存更新策略**：新数据到达时如何更新缓存？追加还是替换？

