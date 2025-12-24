# Change: 迁移 wealthdata 方法到 SDK 和策略框架

## Why

根据 wealthdata package 的分工决策，需要将 wealthdata 方法按照职责划分迁移到不同的模块：

1. **SDK 方法**：数据访问相关的方法（get_price, get_bars, get_all_securities 等）应迁移到 Python SDK，作为独立的数据访问接口，可在不同实现层（回测、模拟交易、实盘）复用。

2. **策略框架方法**：上下文管理和数据转换方法（set_context, get_context, clear_context, bars_to_dataframe）应保留在策略执行引擎框架中，作为框架内部的基础设施。

3. **架构清晰化**：按照架构图（策略 -> 框架.SDK -> 实现层 -> 三方能力）的层次结构，明确各层职责，实现更好的模块化和可维护性。

## What Changes

### 方法迁移划分

**迁移到 Python SDK 的方法**（优先级 0-4）：
- `get_price` - 获取K线/价格数据（优先级 0）
- `get_bars` - 获取K线/Bar对象（优先级 0）
- `get_all_securities` - 查询所有支持的证券基础信息（优先级 2）
- `get_trade_days` - 获取交易日历（优先级 2）
- `get_index_stocks` - 查询某指数成分股列表（优先级 3）
- `get_index_weights` - 查询某指数成分股权重（优先级 3）
- `get_fundamentals` - 查询基本面数据（优先级 4）
- `get_industry` - 行业分类信息查询（优先级 4）
- `get_trades` - 获取成交记录（优先级 1）

**保留在策略框架的方法**（优先级 0）：
- `set_context` - 设置当前线程wealthdata上下文
- `get_context` - 获取当前线程wealthdata上下文
- `clear_context` - 清除当前线程wealthdata上下文（防止泄漏）
- `bars_to_dataframe` - 将Bar对象列表转换为pandas DataFrame

### 架构调整

1. **Python SDK 层**：提供独立的数据访问接口，不依赖策略执行引擎的 Context
2. **策略框架层**：提供上下文管理和数据转换工具，作为框架基础设施
3. **实现层**：回测、模拟交易、实盘等实现层通过适配器模式使用 SDK 方法

### 规范文档更新

基于架构图规划，更新以下规范文档：
- Python SDK 规范：定义 SDK 数据访问方法的接口和行为
- 策略执行引擎规范：定义框架上下文管理方法的接口和行为
- 策略开发规范：更新 wealthdata 模块的使用说明

## Impact

### 受影响的规范
- `openspec/specs/python-sdk/spec.md` - 新增 wealthdata 数据访问方法规范
- `openspec/specs/strategy-engine/spec.md` - 更新上下文管理方法规范
- `openspec/specs/strategy-development/spec.md` - 更新 wealthdata 使用说明

### 受影响的代码
- `engine/wealthdata/wealthdata.py` - 方法实现需要重构和迁移
- `engine/python_sdk/` - 需要新增数据访问接口
- `engine/context/context.py` - 可能需要调整上下文管理方式
- `wealthdata.py` - 顶层模块需要更新导入路径

### 向后兼容性
- **BREAKING**：策略代码中的 `from wealthdata import *` 导入路径可能发生变化
- 需要提供迁移指南，确保现有策略代码可以平滑迁移
- SDK 方法接口保持与现有实现兼容，仅改变实现位置


