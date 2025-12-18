# Change: 扩展 wealthdata 支持更多 jqdatasdk API

## Why

当前 `wealthdata` 兼容层只支持 `get_price()` 和 `get_bars()` 两个最常用的 API，但 JoinQuant 的 jqdatasdk 提供了更多 API，如：

- `get_fundamentals()` - 财务数据查询
- `get_all_securities()` - 获取所有证券信息
- `get_index_stocks()` - 获取指数成分股
- `get_industry()` - 行业分类查询
- `get_trade_days()` - 交易日查询
- `get_index_weights()` - 指数权重查询
- 等等

为了吸引更多 JoinQuant 用户迁移到我们的平台，需要扩展 `wealthdata` 模块，支持更多 jqdatasdk 常用 API，让用户能够：

1. **减少迁移成本**：支持更多 API 意味着需要修改的代码更少
2. **提高兼容性**：覆盖更多 JoinQuant 策略中常用的 API
3. **降低学习成本**：用户可以使用熟悉的 API，无需学习新的接口

**核心目标**：扩展 wealthdata 兼容层，支持 jqdatasdk 的核心 API，实现更高程度的代码兼容性。

## What Changes

- **ADDED**: `get_fundamentals()` - 财务数据查询（适配加密货币场景）
- **ADDED**: `get_all_securities()` - 获取所有交易对信息
- **ADDED**: `get_index_stocks()` - 获取指数成分（适配加密货币指数）
- **ADDED**: `get_trade_days()` - 交易日查询（适配加密货币 7x24 交易）
- **ADDED**: `get_industry()` - 行业分类查询（适配加密货币分类）
- **ADDED**: `get_index_weights()` - 指数权重查询
- **MODIFIED**: `wealthdata` 模块扩展，增加更多 API 函数
- **MODIFIED**: 更新策略开发规范，说明新增 API 的使用方法
- **MODIFIED**: 更新 JoinQuant 迁移指南，说明新增 API 的兼容性

**Non-Breaking**: 现有 API 保持不变，新增 API 作为可选扩展

## Impact

- **Affected specs**: 
  - `strategy-development` - 更新 wealthdata API 使用说明
  - `python-sdk` - 可能需要扩展 Context 或数据源以支持新 API
- **Affected code**: 
  - `engine/wealthdata/wealthdata.py` - 添加新 API 函数实现
  - `PRD/JoinQuant迁移指南.md` - 更新 API 兼容性说明
- **Affected docs**: 
  - `PRD/JoinQuant迁移指南.md` - 更新支持的 API 列表
  - `openspec/specs/strategy-development/spec.md` - 更新 wealthdata API 文档

## Design Considerations

### 核心设计原则

1. **接口兼容性优先**：新 API 的函数签名和返回值格式应与 jqdatasdk 保持一致
2. **数据适配**：由于我们是加密货币交易，需要将股票相关的概念适配到加密货币场景
3. **渐进式支持**：优先支持最常用的 API，其他 API 可以逐步添加
4. **错误处理**：对于不适用或无法实现的 API，提供明确的错误提示或警告

### API 适配策略

#### 1. get_fundamentals() - 财务数据
- **股票场景**：查询公司财务数据（营收、利润等）
- **加密货币适配**：可以返回交易对的基本信息（如市值、24h 成交量等），或返回空数据并提示不适用

#### 2. get_all_securities() - 所有证券
- **股票场景**：返回所有股票代码和基本信息
- **加密货币适配**：返回所有支持的交易对列表和基本信息

#### 3. get_index_stocks() - 指数成分股
- **股票场景**：返回指数成分股列表
- **加密货币适配**：返回加密货币指数（如 BTC 指数、ETH 指数）的成分交易对

#### 4. get_trade_days() - 交易日
- **股票场景**：返回交易日列表（排除周末和节假日）
- **加密货币适配**：加密货币 7x24 交易，可以返回连续的时间序列或提示不适用

#### 5. get_industry() - 行业分类
- **股票场景**：返回股票所属行业
- **加密货币适配**：返回加密货币分类（如 DeFi、Layer1、Layer2 等）

#### 6. get_index_weights() - 指数权重
- **股票场景**：返回指数成分股的权重
- **加密货币适配**：返回加密货币指数成分的权重

### 实现优先级

**Phase 1（高优先级）**：
- `get_all_securities()` - 最常用，实现相对简单
- `get_trade_days()` - 常用，适配相对简单

**Phase 2（中优先级）**：
- `get_index_stocks()` - 需要定义加密货币指数概念
- `get_index_weights()` - 依赖指数数据

**Phase 3（低优先级）**：
- `get_fundamentals()` - 需要定义加密货币"财务数据"概念
- `get_industry()` - 需要定义加密货币分类体系

## Risks / Trade-offs

### Risk: 概念不匹配
**问题**：股票市场的概念（如财务数据、行业分类）与加密货币不完全匹配

**缓解措施**：
- 提供明确的适配说明和警告
- 对于无法适配的 API，返回空数据或抛出明确的异常
- 在文档中说明适配策略和限制

### Risk: 数据源限制
**问题**：某些 API 需要额外的数据源（如指数数据、分类数据）

**缓解措施**：
- 优先实现不需要额外数据源的 API
- 对于需要额外数据的 API，可以先返回空数据或占位数据
- 后续可以通过配置或数据源扩展来完善

### Risk: API 行为差异
**问题**：我们的实现可能与 jqdatasdk 的行为有细微差异

**缓解措施**：
- 详细记录每个 API 的行为差异
- 提供测试用例验证兼容性
- 在迁移指南中明确说明差异

## Migration Plan

### Phase 1: 核心 API 实现
- 实现 `get_all_securities()` 和 `get_trade_days()`
- 更新文档和测试

### Phase 2: 指数相关 API
- 实现 `get_index_stocks()` 和 `get_index_weights()`
- 定义加密货币指数概念

### Phase 3: 高级 API
- 实现 `get_fundamentals()` 和 `get_industry()`
- 完善数据适配和错误处理

### Rollback
- 新 API 作为可选扩展，不影响现有功能
- 如果某个 API 实现有问题，可以暂时返回空数据或抛出异常

## Open Questions (已部分解答)

1. ✅ **数据源**（已明确）：
   - `get_all_securities()`: 从 `ExecRequest.market_data_context` 提取所有交易对
   - `get_trade_days()`: 从 `ExecRequest.market_data_context` 的时间范围生成
   - `get_index_stocks()`: 需要配置文件（Phase 2 定义）
   - `get_index_weights()`: 需要配置文件（Phase 2 定义）
   - `get_industry()`: 需要配置文件（Phase 3 定义）

2. ✅ **适配程度**（已明确）：
   - `get_fundamentals()`: 返回基本交易对信息或空 DataFrame + 警告（Phase 3）
   - 其他 API: 尽量完全兼容，不适用的参数忽略并警告

3. ✅ **优先级**（已确定）：
   - Phase 1: `get_all_securities()`, `get_trade_days()`（最常用，实现简单）
   - Phase 2: `get_index_stocks()`, `get_index_weights()`（需要指数概念）
   - Phase 3: `get_fundamentals()`, `get_industry()`（概念适配复杂）

## API 验证状态

✅ **已完成 API 验证**：所有 API 的函数签名和返回格式已通过验证，详见 `API验证报告.md`。

