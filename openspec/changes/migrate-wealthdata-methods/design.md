# Design: wealthdata 方法迁移架构设计

## Context

根据 wealthdata package 的分工决策和系统架构图，需要将 wealthdata 方法按照职责划分到不同的模块：

1. **SDK 方法**：数据访问相关方法，应作为独立的 SDK 接口，可在不同实现层复用
2. **策略框架方法**：上下文管理和数据转换方法，应作为框架基础设施

架构层次：
```
策略
  ↓
框架.SDK（封装/胶水层）
  ↓
实现层（回测 impl, mock trade impl, real trade impl）
  ↓
三方能力（backtrador, testnet, main net）
```

## Goals / Non-Goals

### Goals
- 明确 SDK 和策略框架的职责边界
- 实现数据访问方法的独立性和可复用性
- 保持策略代码的向后兼容性
- 建立清晰的架构层次和模块划分

### Non-Goals
- 不改变现有方法的接口签名和行为
- 不改变策略开发者的使用方式（通过 wealthdata 模块）
- 不引入新的依赖或框架

## Decisions

### Decision 1: SDK 方法的数据源抽象

**决策**：SDK 方法通过适配器模式获取数据，而不是直接依赖 Context。

**理由**：
- SDK 方法应独立于策略执行引擎，可在不同场景下使用
- 适配器模式允许不同实现层（回测、模拟、实盘）提供不同的数据源
- 保持 SDK 的通用性和可测试性

**实现方式**：
- 定义数据访问适配器接口（DataAdapter）
- 策略框架在设置 Context 时注册数据适配器
- SDK 方法通过适配器获取数据，而不是直接访问 Context

**替代方案**：
- 方案 A：SDK 方法直接依赖 Context（当前实现）
  - 优点：实现简单
  - 缺点：SDK 与策略框架耦合，无法独立使用
- 方案 B：SDK 方法通过全局注册表获取数据源
  - 优点：解耦 Context
  - 缺点：全局状态管理复杂，线程安全问题

**选择方案**：适配器模式，平衡了解耦和实现的简洁性。

### Decision 2: 策略框架方法的保留位置

**决策**：上下文管理方法（set_context, get_context, clear_context）和工具方法（bars_to_dataframe）保留在策略框架中。

**理由**：
- 这些方法是策略执行引擎的基础设施，与引擎生命周期紧密相关
- 不需要在不同实现层复用，仅在策略执行时使用
- 保持框架内部实现细节的封装

**实现方式**：
- 继续在 `engine/wealthdata/wealthdata.py` 中实现，或迁移到 `engine/context/` 模块
- 通过线程局部存储管理 Context
- 策略框架在执行策略前设置 Context，执行后清理

### Decision 3: wealthdata 模块的兼容层设计

**决策**：保留顶层 `wealthdata.py` 作为兼容层，统一导出所有方法。

**理由**：
- 保持策略代码的向后兼容性
- 策略开发者无需关心方法的具体实现位置
- 提供统一的导入接口

**实现方式**：
- `wealthdata.py` 从 SDK 和策略框架模块导入方法
- 保持 `from wealthdata import *` 的使用方式不变
- 内部实现可以逐步迁移，对外接口保持一致

### Decision 4: 数据适配器的注册机制

**决策**：数据适配器通过线程局部存储注册，SDK 方法通过线程局部存储获取。

**理由**：
- 支持多线程并发执行策略
- 每个线程有独立的数据适配器实例
- 避免全局状态导致的线程安全问题

**实现方式**：
```python
# 线程局部存储
_adapter_local = threading.local()

def register_data_adapter(adapter: DataAdapter):
    _adapter_local.adapter = adapter

def get_data_adapter() -> DataAdapter:
    adapter = getattr(_adapter_local, 'adapter', None)
    if adapter is None:
        raise RuntimeError("Data adapter not registered")
    return adapter
```

## Risks / Trade-offs

### Risk 1: 迁移过程中的兼容性问题

**风险**：现有策略代码可能因为导入路径变化而无法运行。

**缓解措施**：
- 保持顶层 `wealthdata.py` 兼容层
- 提供详细的迁移指南
- 在迁移期间同时支持新旧两种实现方式

### Risk 2: 适配器模式的性能开销

**风险**：通过适配器获取数据可能增加一层间接调用，影响性能。

**缓解措施**：
- 适配器调用是简单的函数调用，开销可忽略
- 在关键路径上进行性能测试
- 如果性能成为瓶颈，可以考虑内联优化

### Risk 3: 线程局部存储的内存泄漏

**风险**：如果 Context 清理不当，可能导致线程局部存储泄漏。

**缓解措施**：
- 策略框架必须使用 try-finally 确保清理
- 添加单元测试验证清理逻辑
- 在文档中明确清理责任

## Migration Plan

### Phase 1: 准备阶段
1. 定义数据适配器接口
2. 创建 SDK 数据访问模块结构
3. 更新规范文档

### Phase 2: 实现阶段
1. 实现数据适配器接口
2. 迁移 SDK 方法到新模块
3. 更新策略框架的适配器注册逻辑
4. 更新顶层 wealthdata 模块的导入

### Phase 3: 测试阶段
1. 单元测试验证方法功能
2. 集成测试验证策略执行
3. 性能测试验证开销

### Phase 4: 迁移阶段
1. 更新文档和迁移指南
2. 逐步迁移现有策略代码
3. 移除旧实现（如果适用）

## Open Questions

1. **数据适配器的生命周期**：适配器是否需要在每次策略执行时重新创建，还是可以复用？
   - 建议：每次执行时创建，确保数据隔离

2. **SDK 方法的错误处理**：当数据适配器未注册时，应该抛出异常还是返回默认值？
   - 建议：抛出明确的异常，帮助开发者发现问题

3. **bars_to_dataframe 的位置**：是否应该迁移到 SDK，因为它是数据转换工具？
   - 建议：保留在策略框架，因为它是框架内部使用的工具方法


