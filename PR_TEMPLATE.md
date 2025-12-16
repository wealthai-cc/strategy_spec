# 策略执行引擎框架规范（类似 JoinQuant）

## 📋 变更概述

添加策略执行引擎框架规范，参考 JoinQuant 平台设计，提供简化的策略开发接口。让开发者可以通过 Python 文件编写策略，无需直接实现 gRPC 服务。

## ✨ 主要变更

### 新增规范文档

- **`openspec/specs/strategy-development/spec.md`** - 策略开发规范
  - 生命周期函数规范（initialize, handle_bar, on_order, on_risk_event）
  - Context 对象接口（账户、行情、下单）
  - Python 策略文件编写规范
  - 完整的策略开发示例和最佳实践

- **`PRD/策略开发快速开始.md`** - 快速开始指南
  - 快速上手教程
  - 常用代码示例
  - 常见问题解答

### 更新的规范文档

- **`openspec/specs/strategy-engine/spec.md`**
  - 添加策略执行引擎架构说明
  - 添加事件到函数的映射规则
  - 添加执行流程说明

- **`openspec/project.md`**
  - 添加策略开发框架说明
  - 添加策略执行引擎依赖说明

- **其他规范文档**
  - 更新了 account、order、market-data、python-sdk 规范的交叉引用

### 提案文档

- **`openspec/changes/add-strategy-execution-framework/`**
  - proposal.md - 变更原因和影响
  - design.md - 技术设计决策
  - tasks.md - 实现任务清单
  - specs/ - 规范变更（delta）

## 🎯 设计目标

1. **简化开发**：策略开发者只需写 Python 文件，无需了解底层 gRPC
2. **生命周期驱动**：通过生命周期函数组织策略逻辑
3. **事件自动调度**：框架自动将触发事件映射到对应函数
4. **统一接口**：Context 对象提供统一的账户、行情、下单接口
5. **环境一致性**：同一策略代码可在回测、仿真、实盘运行

## 🏗️ 架构设计

```
策略管理系统
    ↓ (gRPC)
StrategySpec.Exec(ExecRequest)
    ↓
策略执行引擎（Engine）
    ├── 策略加载器（Strategy Loader）
    ├── 事件调度器（Event Dispatcher）
    ├── Context 管理器（Context Manager）
    └── 生命周期管理器（Lifecycle Manager）
    ↓
Python 策略文件
    ├── initialize(context)
    ├── handle_bar(context, bar)
    ├── on_order(context, order)
    └── on_risk_event(context, event)
```

## 📝 核心特性

### 生命周期函数

- `initialize(context)` - 策略初始化（必需）
- `before_trading(context)` - 交易前准备（可选）
- `handle_bar(context, bar)` - 处理 K 线数据（可选）
- `on_order(context, order)` - 处理订单状态变更（可选）
- `on_risk_event(context, event)` - 处理风控事件（可选）

### Context 对象

提供统一的接口：
- `context.account` - 账户信息
- `context.history()` - 历史行情数据
- `context.order_buy()` / `context.order_sell()` - 下单接口
- `context.cancel_order()` - 撤单接口

## 🔍 审查说明

- ✅ 所有规范文档已更新
- ✅ 交叉引用已完善
- ✅ 示例代码已添加
- ✅ 快速开始指南已创建

## 📚 相关文档

- [策略开发规范](./openspec/specs/strategy-development/spec.md)
- [策略执行引擎规范](./openspec/specs/strategy-engine/spec.md)
- [策略开发快速开始](./PRD/策略开发快速开始.md)
- [提案文档](./openspec/changes/add-strategy-execution-framework/proposal.md)

## ✅ 检查清单

- [x] 规范文档已更新
- [x] 交叉引用已完善
- [x] 示例代码已添加
- [x] 快速开始指南已创建
- [x] 代码已提交并推送

## 🚀 后续工作

代码实现阶段（待评审通过后）：
- [ ] 实现策略执行引擎（Python）
- [ ] 实现 Context 对象
- [ ] 实现策略加载器
- [ ] 实现事件调度器
- [ ] 添加单元测试和集成测试

---

**变更类型**：新增功能（Non-Breaking）  
**影响范围**：策略开发接口、执行引擎架构  
**向后兼容**：是（现有 gRPC 接口保持不变）

