## MODIFIED Requirements

### Requirement: Context 线程局部存储管理

策略执行引擎 SHALL 管理 Context 对象在线程局部存储中的生命周期，以支持 wealthdata 兼容模块。

#### Scenario: 设置 Context
- **WHEN** 引擎开始执行策略函数
- **THEN** 引擎 SHALL 在执行前将 Context 设置到线程局部存储
- **AND** 引擎 SHALL 注册数据适配器到线程局部存储
- **AND** 数据适配器 SHALL 从 ExecRequest 的 market_data_context 获取数据

#### Scenario: 清理 Context
- **WHEN** 策略执行完成（成功或失败）
- **THEN** 引擎 SHALL 清理线程局部存储中的 Context
- **AND** 引擎 SHALL 清理线程局部存储中的数据适配器
- **AND** 引擎 SHALL 清理线程局部存储中的策略模块引用

#### Scenario: 异常情况下的清理
- **WHEN** 策略执行抛出异常
- **THEN** 引擎 SHALL 确保 Context 被正确清理（使用 finally 块）
- **AND** 引擎 SHALL 确保数据适配器被正确清理
- **AND** 引擎 SHALL 确保策略模块引用被正确清理

## ADDED Requirements

### Requirement: 上下文管理方法

策略执行引擎框架 SHALL 提供上下文管理方法，用于设置、获取和清理当前线程的 wealthdata 上下文。

#### Scenario: 设置上下文
- **WHEN** 策略框架调用 `set_context(context)`
- **THEN** 框架 SHALL 将 Context 对象设置到线程局部存储
- **AND** 框架 SHALL 同时注册数据适配器
- **AND** 优先级为 0（最高优先级）

#### Scenario: 获取上下文
- **WHEN** 策略框架或 wealthdata 方法调用 `get_context()`
- **THEN** 框架 SHALL 从线程局部存储获取 Context 对象
- **AND** 如果 Context 不存在，SHALL 抛出 RuntimeError
- **AND** 优先级为 0（最高优先级）

#### Scenario: 清理上下文
- **WHEN** 策略框架调用 `clear_context()`
- **THEN** 框架 SHALL 从线程局部存储清除 Context 对象
- **AND** 框架 SHALL 清除数据适配器
- **AND** 框架 SHALL 清除策略模块引用
- **AND** 优先级为 0（最高优先级）
- **AND** 用于防止内存泄漏

### Requirement: 数据转换工具方法

策略执行引擎框架 SHALL 提供数据转换工具方法，将 Bar 对象转换为 pandas DataFrame。

#### Scenario: Bar 对象转换为 DataFrame
- **WHEN** 策略框架调用 `bars_to_dataframe(bars)`
- **THEN** 框架 SHALL 将 Bar 对象列表转换为 pandas DataFrame
- **AND** DataFrame SHALL 包含 open, high, low, close, volume 列
- **AND** DataFrame 索引 SHALL 为 DatetimeIndex（基于 close_time）
- **AND** 优先级为 0（最高优先级）

#### Scenario: 空列表处理
- **WHEN** `bars_to_dataframe([])` 被调用
- **THEN** 框架 SHALL 返回空的 DataFrame，包含正确的列结构
- **AND** DataFrame SHALL 包含 open, high, low, close, volume 列


