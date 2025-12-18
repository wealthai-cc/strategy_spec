# Change: 设计可扩展的交易所对接框架

## Why

当前策略规范中，`exchange` 字段和 Python SDK 的 `broker` 参数设计为支持多个交易所，但缺少明确的扩展机制和设计原则。为了支持 Binance 等主流交易所，并确保未来能够轻松扩展支持新交易所，需要：

1. **明确扩展机制**：定义如何添加新交易所支持的标准化流程
2. **统一接口抽象**：确保不同交易所的差异通过统一接口处理
3. **Binance 优先支持**：主要对接 Binance，作为参考实现
4. **可扩展架构**：设计支持未来添加 OKX、Bybit 等交易所的架构

## What Changes

- **ADDED**: 交易所扩展机制规范（如何添加新交易所）
- **MODIFIED**: `ExecRequest.exchange` 字段支持扩展的交易所标识规范
- **MODIFIED**: Python SDK 的 `get_trading_rule()` 和 `get_commission_rates()` 支持扩展的交易所
- **ADDED**: 交易所适配层设计原则（统一接口，差异处理）
- **ADDED**: Binance 作为主要支持的交易所，提供完整实现示例
- **MODIFIED**: 项目文档明确说明扩展机制和 Binance 优先支持

**Non-Breaking**: 现有使用 "binance" 的代码继续有效，新增扩展机制

## Impact

- **Affected specs**: 
  - `strategy-engine` - ExecRequest 的 exchange 字段扩展规范
  - `python-sdk` - broker 参数扩展机制和适配层设计
  - `project` - 交易所扩展机制和 Binance 优先支持说明
- **Affected code**: 
  - `strategy_spec.proto` - exchange 字段注释和扩展说明
  - Python SDK 实现 - 交易所适配层架构
  - 策略管理系统 - 交易所配置和路由逻辑
- **Affected docs**: 
  - `README.md` - 交易所支持说明
  - `openspec/project.md` - 更新项目上下文和扩展机制
  - 新增交易所扩展指南文档

## Design Considerations

### 核心设计原则

1. **统一接口抽象**：所有交易所通过统一的接口规范交互
2. **差异隔离**：交易所特定差异通过适配层处理，不暴露给策略
3. **Binance 优先**：Binance 作为主要支持的交易所，提供完整参考实现
4. **可扩展性**：新交易所通过标准化流程添加，最小化对现有代码的影响

### 交易所标识规范

- 使用小写字符串标识：`binance`, `okx`, `bybit` 等
- 标识必须唯一且稳定
- 支持通过配置扩展新交易所

### 适配层设计

- Python SDK 提供交易所适配层
- 每个交易所实现统一的接口（trading rules, commission rates）
- 差异通过适配层统一处理

