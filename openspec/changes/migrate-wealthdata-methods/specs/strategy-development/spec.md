## MODIFIED Requirements

### Requirement: wealthdata 兼容模块（JoinQuant 兼容）

策略 SHALL 使用 `wealthdata` 模块进行数据访问，提供与 JoinQuant jqdatasdk 兼容的接口。

**所有 JoinQuant 兼容的 API SHALL 在 `wealthdata` 模块中定义，策略 SHALL 通过 `from wealthdata import *` 访问所有功能。**

#### Scenario: 策略导入所有 JoinQuant API
- **WHEN** 策略执行 `from wealthdata import *`
- **THEN** 所有 JoinQuant 兼容的 API 都可用，包括数据访问函数、策略函数和配置函数
- **AND** SDK 数据访问方法通过数据适配器获取数据
- **AND** 策略框架上下文管理方法由引擎自动调用

#### Scenario: 数据访问方法使用
- **WHEN** 策略调用 `get_price()`, `get_bars()`, `get_all_securities()` 等 SDK 方法
- **THEN** 方法 SHALL 通过数据适配器获取数据
- **AND** 数据适配器由策略框架在执行前自动注册
- **AND** 方法 SHALL 返回与现有实现兼容的结果

#### Scenario: 上下文管理方法使用
- **WHEN** 策略需要访问 Context 对象
- **THEN** 策略可以通过 `get_context()` 获取当前 Context
- **AND** Context 由策略框架在执行前自动设置
- **AND** Context 在策略执行完成后自动清理

#### Scenario: 数据转换工具使用
- **WHEN** 策略需要将 Bar 对象转换为 DataFrame
- **THEN** 策略可以调用 `bars_to_dataframe(bars)`
- **AND** 方法 SHALL 返回 pandas DataFrame，包含正确的列和索引

### Requirement: 数据访问方法优先级

wealthdata 数据访问方法 SHALL 按照优先级实现，确保核心功能优先支持。

#### Scenario: 优先级 0 方法（最高优先级）
- **WHEN** 策略使用 `get_price()` 或 `get_bars()`
- **THEN** 这些方法 SHALL 优先实现和测试
- **AND** 这些方法 SHALL 提供完整的功能和错误处理

#### Scenario: 优先级 1 方法（高优先级）
- **WHEN** 策略使用 `get_trades()`
- **THEN** 这些方法 SHALL 在优先级 0 方法之后实现
- **AND** 这些方法 SHALL 提供完整的功能

#### Scenario: 优先级 2 方法（中等优先级）
- **WHEN** 策略使用 `get_all_securities()` 或 `get_trade_days()`
- **THEN** 这些方法 SHALL 在优先级 1 方法之后实现
- **AND** 这些方法 SHALL 提供基本功能

#### Scenario: 优先级 3 方法（较低优先级）
- **WHEN** 策略使用 `get_index_stocks()` 或 `get_index_weights()`
- **THEN** 这些方法 SHALL 在优先级 2 方法之后实现
- **AND** 这些方法 SHALL 可以返回简化实现或配置数据

#### Scenario: 优先级 4 方法（最低优先级）
- **WHEN** 策略使用 `get_fundamentals()` 或 `get_industry()`
- **THEN** 这些方法 SHALL 在优先级 3 方法之后实现
- **AND** 这些方法 SHALL 可以返回警告或简化实现

