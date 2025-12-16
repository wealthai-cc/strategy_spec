# Change: 添加策略执行引擎框架（类似 JoinQuant）

## Why

当前策略规范定义了 gRPC 接口（StrategySpec），但缺少类似 JoinQuant 的策略开发框架，使得策略开发者需要直接实现 gRPC 服务，开发门槛较高。需要提供一个策略执行引擎框架，让开发者可以：

1. **简化策略开发**：通过 Python 文件编写策略，无需了解 gRPC 细节
2. **生命周期管理**：提供 initialize、before_trading、handle_bar 等生命周期函数
3. **自动事件调度**：框架自动将触发事件转换为策略函数调用
4. **统一 Context 对象**：提供账户、行情、下单等统一接口
5. **支持回测和实盘**：同一策略代码可在不同环境运行

## What Changes

- **ADDED**: 策略开发接口规范（Python 策略代码编写规范）
- **ADDED**: 策略生命周期函数规范（initialize, before_trading, handle_bar, on_order, on_risk_event）
- **ADDED**: Context 对象设计（账户、行情、下单接口）
- **ADDED**: 策略执行引擎架构（如何加载和执行 Python 策略）
- **MODIFIED**: StrategySpec 接口说明（引擎作为策略实现，将 Python 策略转换为 gRPC 调用）
- **ADDED**: 事件调度机制（如何将 ExecRequest 转换为策略函数调用）

**Non-Breaking**: 现有 gRPC 接口保持不变，引擎作为策略实现层

## Impact

- **Affected specs**: 
  - `strategy-engine` - 添加引擎架构说明
  - `strategy-development` - 新增策略开发规范
  - `project` - 更新项目架构说明
- **Affected code**: 
  - 新增策略执行引擎实现（Python）
  - 新增策略开发 SDK（Context 对象、下单接口等）
  - 策略管理系统集成引擎
- **Affected docs**: 
  - 新增策略开发指南
  - 更新架构文档
  - 添加策略示例代码

## Design Considerations

### 核心设计原则

1. **简化开发**：策略开发者只需写 Python 文件，无需了解底层 gRPC
2. **生命周期驱动**：通过生命周期函数组织策略逻辑
3. **事件自动调度**：框架自动将触发事件映射到对应函数
4. **统一接口**：Context 对象提供统一的账户、行情、下单接口
5. **环境一致性**：同一策略代码可在回测、仿真、实盘运行

### 架构层次

```
策略管理系统
    ↓
StrategySpec (gRPC 接口)
    ↓
策略执行引擎（Engine）
    ├── 策略加载器（Strategy Loader）
    ├── 事件调度器（Event Dispatcher）
    ├── Context 管理器（Context Manager）
    └── 生命周期管理器（Lifecycle Manager）
    ↓
Python 策略代码
    ├── initialize(context)
    ├── before_trading(context)
    ├── handle_bar(context, bar)
    ├── on_order(context, order)
    └── on_risk_event(context, event)
```

### 与现有接口的关系

- StrategySpec.Exec 接口保持不变
- 引擎作为策略实现，将 Python 策略转换为 Exec 调用
- 引擎内部处理事件调度和生命周期管理
- 策略开发者无需直接实现 gRPC 服务

