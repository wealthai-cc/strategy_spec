# WealthAI 策略规范 - OpenSpec 主规格

> 本文档为 WealthAI 策略规范（Strategy Spec）的主规格索引，遵循 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 规范进行需求与开发迭代管理。

## 项目概述

WealthAI 策略规范定义了面向策略实现者的公共接口规范（Proto3），用于在策略与策略管理系统之间进行标准化交互。设计目标为无状态、可测试、跨语言、可扩展，易于在不同运行环境（回测、仿真、真实交易）复用。

## 规格文档索引

### 核心模块

- **[策略执行引擎规范](../openspec/specs/strategy-engine/spec.md)** (`openspec/specs/strategy-engine/spec.md`)
  - 策略服务接口（Health/Exec）
  - 触发机制（行情/风控/订单状态）
  - 执行请求与响应结构
  - 策略执行引擎架构（类似 JoinQuant）
  - 并发与幂等约定

- **[策略开发规范](../openspec/specs/strategy-development/spec.md)** (`openspec/specs/strategy-development/spec.md`)
  - 生命周期函数（initialize, handle_bar, on_order 等）
  - Context 对象接口（账户、行情、下单）
  - wealthdata 兼容模块（JoinQuant 零代码迁移）
  - Python 策略文件编写规范
  - 策略开发示例

- **[账户与持仓规范](../openspec/specs/account/spec.md)** (`openspec/specs/account/spec.md`)
  - 账户类型与货币类型
  - 余额与持仓数据结构
  - 风控指标（保证金率、风险度、杠杆等）

- **[订单管理规范](../openspec/specs/order/spec.md)** (`openspec/specs/order/spec.md`)
  - 订单类型（市价/限价/止损）
  - 订单状态流转
  - 订单操作事件（创建/撤销/修改）
  - 价格字段与执行信息

- **[行情数据规范](../openspec/specs/market-data/spec.md)** (`openspec/specs/market-data/spec.md`)
  - Bar（K线）数据结构
  - 技术指标（MA/EMA）
  - 多分辨率行情上下文

- **[Python SDK 规范](../openspec/specs/python-sdk/spec.md)** (`openspec/specs/python-sdk/spec.md`)
  - TradingRule 查询接口
  - 佣金费率查询接口
  - 本地缓存与并发安全

### 参考文档

- **[策略开发快速开始](./策略开发快速开始.md)** (`策略开发快速开始.md`)
  - 快速上手编写 Python 策略
  - 生命周期函数使用示例
  - Context 对象使用指南

- **[JoinQuant 迁移指南](./JoinQuant迁移指南.md)** (`JoinQuant迁移指南.md`)
  - JoinQuant 用户零代码迁移指南
  - wealthdata 兼容层使用说明
  - API 对比和迁移检查清单

- **[示例文档](./spec_example.md)** (`spec_example.md`)
  - 策略下单接口示例
  - 完整的 OpenSpec 结构参考

## 设计原则

1. **无状态策略**：策略不保存内部状态，每次 `Exec` 为纯函数式调用，由入参决定行为
2. **风控内部化**：风控逻辑在策略内部闭环，对外仅通过订单事件体现
3. **时间统一**：所有时间字段使用 Unix 毫秒时间戳
4. **明确触发**：支持行情、风控、订单状态三类触发，触发详情通过 `TriggerDetail` 描述

## 版本管理

- **语义化版本**：变更遵循 `MAJOR.MINOR.PATCH`
- **兼容性约定**：
  - 添加字段：默认向后兼容（保留已有字段与语义）
  - 删除/重命名字段：视为破坏性变更，需升级主版本并提供迁移建议

## 变更流程

1. **需求/特性提出**：以 OpenSpec 规范撰写详细需求，并提交 PR
2. **评审与共识**：相关方基于规格文档在线异步 Review 达成共识并记录"决议"
3. **开发与交付**：代码实现严格对应规格落点，强制规格先行，代码后行
4. **验收与回溯**：所有 Feature 必须有对应的规格快照历史，确保可追溯与复盘

## 相关资源

- **[如何提需求](./如何提需求.md)** - 使用 OpenSpec 提需求的完整指南（**新手指南**）
- [开发范式文档](./开发范式文档.md) - OpenSpec 交互入口与规范约定
- [审查报告](./审查报告.md) - OpenSpec 文档审查与评审记录
- [README.md](../README.md) - 项目总体说明
- [review.md](../review.md) - 规范评审与改进建议

## 贡献指南

- 所有新增特性、改动及评审讨论均通过 PR 方式跟踪，并在规格文件中同步描述
- 请遵循现有风格与注释规范：所有标识符与字段保留中文注释
- 欢迎通过 Issue/PR 提交改进建议或扩展（指标、订单字段、错误模型等）

---

**最后更新**：2025-12-15  
**维护者**：WealthAI 团队

