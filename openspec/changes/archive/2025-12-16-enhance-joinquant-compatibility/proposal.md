# Change: 增强 JoinQuant 兼容性

## Why

通过分析从 JoinQuant 直接复制的策略代码（如 `double_mean.py`），发现当前框架与 JoinQuant 存在多处不兼容，导致用户无法直接迁移策略代码。主要问题包括：

1. **缺少定时运行机制**：JoinQuant 的 `run_daily()` 允许在特定时间点运行函数（开盘前、开盘时、收盘后），我们的框架只支持事件驱动的生命周期函数
2. **缺少便捷下单 API**：JoinQuant 提供 `order_value()`（按金额下单）和 `order_target()`（目标持仓下单），我们的框架只有基础的 `order_buy()` 和 `order_sell()`
3. **Context 属性不完整**：缺少 `context.current_dt`（当前时间）、`context.portfolio.available_cash`（可用现金）、`context.portfolio.positions_value`（持仓市值）等常用属性
4. **缺少全局变量支持**：JoinQuant 使用 `g` 全局变量对象存储策略状态，我们的框架只支持 `context` 属性存储
5. **缺少日志模块**：JoinQuant 提供 `log` 模块用于日志记录，我们的框架没有提供
6. **API 参数差异**：`get_bars()` 使用 `unit` 参数，而我们的框架使用 `frequency`
7. **持仓访问方式不同**：JoinQuant 支持 `context.portfolio.positions[security]` 字典式访问，我们的框架使用列表
8. **缺少成交记录查询**：JoinQuant 提供 `get_trades()` 获取成交记录，我们的框架没有提供

这些问题严重阻碍了 JoinQuant 用户的迁移，需要扩展框架以提供更好的兼容性。

**核心目标**：增强策略框架的 JoinQuant 兼容性，让用户能够以最小修改迁移策略代码，降低迁移成本。

**重要背景**：框架需要同时支持股票市场（美股、港股、A股）和加密货币市场。股票市场与 JoinQuant 保持一致，加密货币市场需要根据 7x24 交易、无开盘收盘等特性进行调整。

## What Changes

### 新增功能

- **ADDED**: `run_daily()` 函数 - 支持定时运行策略函数（开盘前、开盘时、收盘后等）
- **ADDED**: `order_value()` 函数 - 按金额下单（自动计算数量）
- **ADDED**: `order_target()` 函数 - 目标持仓下单（自动计算买卖数量）
- **ADDED**: `g` 全局变量对象 - 支持策略级别的全局变量存储
- **ADDED**: `log` 模块 - 提供日志记录功能（`log.info()`, `log.warn()`, `log.error()` 等）
- **ADDED**: `get_trades()` 函数 - 获取成交记录
- **ADDED**: Context 属性扩展：
  - `context.current_dt` - 当前时间（datetime 对象）
  - `context.portfolio.available_cash` - 可用现金
  - `context.portfolio.positions_value` - 持仓市值
  - `context.portfolio.positions` - 支持字典式访问（`positions[symbol]`）
- **ADDED**: `get_bars()` 参数兼容 - 支持 `unit` 参数（作为 `frequency` 的别名）
- **ADDED**: 市场类型识别机制 - 自动识别股票市场和加密货币市场
- **ADDED**: 市场类型自适应处理 - 根据市场类型调整定时运行、交易日等逻辑

### 修改功能

- **MODIFIED**: `Portfolio` 类 - 添加 `available_cash`、`positions_value` 属性，支持字典式 `positions` 访问
- **MODIFIED**: `Context` 类 - 添加 `current_dt` 属性，从 `current_bar` 自动计算
- **MODIFIED**: `wealthdata.get_bars()` - 支持 `unit` 参数（兼容 `frequency`）
- **MODIFIED**: `run_daily()` - 根据市场类型调整时间匹配逻辑（股票市场匹配实际开盘时间，加密货币市场匹配逻辑时间点）
- **MODIFIED**: `get_trade_days()` - 根据市场类型返回不同的交易日列表（股票市场排除节假日，加密货币市场返回所有日期）

### 可选功能（简化实现）

- **ADDED**: `set_benchmark()` - 设置基准（仅记录，不影响执行）
- **ADDED**: `set_option()` - 设置选项（仅记录，不影响执行）
- **ADDED**: `set_order_cost()` - 设置手续费（仅记录，不影响执行，实际手续费由系统管理）

**Non-Breaking**: 所有新增功能都是可选的，现有策略代码不受影响。

## Impact

- **Affected specs**: 
  - `strategy-development` - 新增 JoinQuant 兼容 API 使用说明
  - `strategy-engine` - 新增定时运行机制和全局变量管理
- **Affected code**: 
  - `engine/context/context.py` - 扩展 Context 和 Portfolio 类
  - `engine/wealthdata/wealthdata.py` - 添加 `get_trades()` 和参数兼容
  - `engine/` - 新增定时运行机制和全局变量管理模块
  - `strategy/` - 可能需要添加兼容性辅助模块
- **Affected docs**: 
  - `PRD/JoinQuant迁移指南.md` - 更新兼容性说明
  - `openspec/specs/strategy-development/spec.md` - 更新 API 文档

## Design Considerations

### 定时运行机制（run_daily）

JoinQuant 的 `run_daily()` 允许在特定时间点运行函数，但我们的框架是事件驱动的。需要设计一个适配层：

- **方案 1**：在 `before_trading` 生命周期中检查并调用注册的定时函数
- **方案 2**：扩展 `ExecRequest` 支持时间触发（需要协议层改动，成本较高）
- **推荐方案**：方案 1，在引擎层面实现定时函数注册和调用逻辑

**市场类型适配**：
- **股票市场**：匹配实际开盘时间（A股 9:30，美股/港股根据时区），只在交易日触发
- **加密货币市场**：匹配逻辑时间点（如 00:00），每天都会触发（7x24 交易）

### 全局变量（g）

- 使用模块级别的全局对象，每个策略文件有独立的 `g` 对象
- 通过策略加载器在加载时注入 `g` 对象到策略模块的命名空间

### 日志模块（log）

- 提供简单的日志模块，支持 `info()`, `warn()`, `error()`, `debug()` 等方法
- 日志输出到标准输出或可配置的输出流
- 可以集成到现有的日志系统（如果有）

### 下单函数（order_value, order_target）

- `order_value()`: 根据金额和当前价格计算数量，调用 `context.order_buy()` 或 `context.order_sell()`
- `order_target()`: 根据目标持仓和当前持仓计算需要买卖的数量，调用相应的下单函数

### Context 属性扩展

- `current_dt`: 从 `current_bar.close_time` 转换而来
- `portfolio.available_cash`: 从 `account.available_margin` 或 `account.balances` 计算
- `portfolio.positions_value`: 从持仓列表计算总市值
- `portfolio.positions`: 提供字典式访问接口，内部维护列表和字典两种结构

## Open Questions

1. **定时运行精度**：`run_daily()` 的时间精度如何保证？是否需要支持更细粒度的时间触发？
   - **答案**：时间精度受限于 `ExecRequest` 的触发时间，通过近似匹配实现。如果需要更精确的触发，可能需要扩展 `ExecRequest` 协议支持时间触发。

2. **全局变量作用域**：`g` 对象的作用域是策略文件级别还是策略实例级别？
   - **答案**：策略文件级别。每个策略文件加载时创建独立的 `g` 对象，不同策略实例之间隔离。

3. **日志级别**：是否需要支持日志级别过滤（如 JoinQuant 的 `log.set_level()`）？
   - **答案**：简化实现，`log.set_level()` 接受调用但不影响输出。未来可根据需求扩展。

4. **成交记录格式**：`get_trades()` 返回的数据格式如何与 JoinQuant 保持一致？
   - **答案**：从 `context._completed_orders` 提取成交记录，转换为 JoinQuant 格式的字典，包含 `security`, `price`, `amount`, `time` 等字段。

5. **市场类型配置**：是否需要支持配置文件或参数显式指定市场类型？
   - **答案**：支持通过 `context` 属性或策略参数显式指定，优先级高于格式识别。

6. **时区处理**：美股和港股涉及不同时区，如何正确处理时区和交易时间？
   - **答案**：使用 `pytz` 库处理时区，为每个市场类型配置对应的时区和交易时间。详见 `design.md`。

7. **交易日历**：股票市场的交易日历数据来源？是否需要支持自定义交易日历？
   - **答案**：使用静态配置文件 + 动态更新机制。支持通过配置文件更新节假日，未来可支持 API 更新。详见 `design.md`。

