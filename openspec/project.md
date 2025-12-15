# Project Context

## Purpose
WealthAI 策略规范（Strategy Spec）定义了面向策略实现者的公共接口规范（Proto3），用于在策略与策略管理系统之间进行标准化交互。设计目标为无状态、可测试、跨语言、可扩展，易于在不同运行环境（回测、仿真、真实交易）复用。

## Tech Stack
- **Protocol Buffers (Proto3)**: 接口定义和数据序列化
- **gRPC**: 服务接口实现
- **Python**: 策略侧 SDK 实现
- **Go**: 协议生成和系统实现（参考）

## Project Conventions

### Code Style
- 所有 Proto 文件使用 Proto3 语法
- 所有标识符与字段保留中文注释（`INVALID_XXX` 占位除外）
- 时间字段统一使用 Unix 毫秒时间戳
- 价格和金额使用 `Currency` 结构保证精度

### Architecture Patterns
- **无状态策略**: 策略不保存内部状态，每次 `Exec` 为纯函数式调用
- **风控内部化**: 风控逻辑在策略内部闭环，对外仅通过订单事件体现
- **明确触发**: 支持行情、风控、订单状态三类触发机制
- **幂等性保证**: 通过 `exec_id` 和 `unique_id` 确保执行和订单的幂等性

### Testing Strategy
- 所有接口变更需保持向后兼容（添加字段默认兼容）
- 破坏性变更需升级主版本并提供迁移建议
- 遵循语义化版本管理（MAJOR.MINOR.PATCH）

### Git Workflow
- 所有新增特性、改动及评审讨论均通过 PR 方式跟踪
- 代码提交需引用/关联相关文档变更记录
- 遵循 OpenSpec 规范进行需求与开发迭代管理

## Domain Context
- **策略执行**: 策略通过 `Exec` 接口接收触发事件，返回订单操作事件
- **账户管理**: 支持模拟账户、现金账户、保证金账户等多种账户类型
- **订单管理**: 支持市价单、限价单、止损市价单、止损限价单
- **行情数据**: 支持多分辨率 K 线数据和技术指标（MA/EMA）
- **风控指标**: 实时计算并传递保证金率、风险度、杠杆等风控指标

## Important Constraints
- **无状态要求**: 策略必须是无状态的，所有状态信息通过 `ExecRequest` 传递
- **并发安全**: 同一账户的同一策略由系统保证串行执行
- **超时控制**: 策略必须在 `max_timeout` 秒内返回响应
- **精度要求**: 价格和金额使用字符串类型保证精度，避免浮点数精度问题

## External Dependencies
- **交易所接口**: 通过 `exchange` 字段标识交易所（如 binance、okx）
- **Python SDK**: 提供 `get_trading_rule` 和 `get_commission_rates` 本地查询接口
- **策略管理系统**: 负责触发策略执行、管理账户和订单状态

## OpenSpec 工作流程
本项目采用 OpenSpec 规范进行需求与开发迭代管理：
- **规格文档**: 位于 `PRD/` 目录，包含主规格索引和各模块详细规范
- **变更提案**: 通过 `openspec/changes/` 目录管理新功能和变更
- **当前规范**: 通过 `openspec/specs/` 目录维护已实现的规范
- **审查报告**: 在 `PRD/审查报告.md` 中记录文档审查和评审结果

详细工作流程请参考 `PRD/开发范式文档.md` 和 `openspec/AGENTS.md`。
