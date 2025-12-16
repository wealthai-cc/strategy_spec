# Change: 明确策略框架专门为 Binance 交易所设计

## Why

当前策略规范中，`exchange` 字段和 Python SDK 的 `broker` 参数设计为支持多个交易所（如 binance、okx），但实际使用场景是专门对接 Binance 交易所。明确 Binance 作为唯一支持的交易所可以：

1. **简化设计**：移除多交易所抽象的复杂性
2. **明确约束**：所有规范和实现都针对 Binance 的特性设计
3. **减少混淆**：开发者明确知道这是 Binance 专用框架
4. **优化实现**：可以针对 Binance 的 API 和特性进行优化

## What Changes

- **MODIFIED**: `ExecRequest.exchange` 字段明确为 Binance 专用，值固定为 "binance"
- **MODIFIED**: Python SDK 的 `get_trading_rule()` 和 `get_commission_rates()` 明确为 Binance 专用，broker 参数固定为 "binance"
- **MODIFIED**: 项目文档明确说明策略框架专门为 Binance 设计
- **MODIFIED**: 所有示例代码统一使用 "binance" 作为交易所标识
- **ADDED**: Binance 特定的约束和说明（如交易规则、API 限制等）

**Non-Breaking**: 现有使用 "binance" 的代码继续有效，只是明确化设计意图

## Impact

- **Affected specs**: 
  - `strategy-engine` - ExecRequest 的 exchange 字段说明
  - `python-sdk` - broker 参数说明和 Binance 特定约束
  - `project` - 项目上下文和约束说明
- **Affected code**: 
  - `strategy_spec.proto` - exchange 字段注释
  - Python SDK 实现 - 明确 Binance 支持
  - 所有示例代码 - 统一使用 "binance"
- **Affected docs**: 
  - `README.md` - 明确 Binance 专用
  - `openspec/project.md` - 更新项目上下文
  - 所有规范文档 - 更新示例和说明

## Design Considerations

### 方案：明确 Binance 专用设计（推荐）

**核心原则**：
- `exchange` 字段值固定为 "binance"
- Python SDK 的 `broker` 参数固定为 "binance"
- 所有规范和实现都针对 Binance 的特性
- 文档明确说明这是 Binance 专用框架

**优点**：
- 简化设计和实现
- 明确设计意图，减少混淆
- 可以针对 Binance 优化
- 向后兼容（现有 "binance" 使用继续有效）

**未来扩展**：
- 如果未来需要支持其他交易所，可以通过新的提案扩展
- 当前设计保持 Binance 专用，避免过度设计

