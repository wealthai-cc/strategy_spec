## ADDED Requirements

### Requirement: wealthdata 模块设置和策略加载

引擎 SHALL 在加载策略文件时设置 `wealthdata` 模块，确保所有 JoinQuant 兼容的 API 都可用。

**所有 JoinQuant 兼容的 API 必须在 `wealthdata` 模块中定义，引擎只负责设置策略特定的实例（g, log），不进行模块注入。**

#### Scenario: 策略加载前设置 wealthdata 模块
- **WHEN** 引擎开始加载策略文件
- **THEN** 引擎 SHALL 在策略加载之前设置 `wealthdata` 模块：
  - 创建策略特定的 `g` 对象并设置到 `wealthdata.g`
  - 创建策略特定的 `log` 对象并设置到 `wealthdata.log`
  - 设置策略模块到线程局部存储（用于 `run_daily`, `set_benchmark` 等）

#### Scenario: 策略导入 wealthdata
- **WHEN** 策略文件执行 `from wealthdata import *`
- **THEN** 策略 SHALL 能够访问所有 JoinQuant 兼容的 API
- **AND** 所有函数和对象都来自 `wealthdata` 模块，无需运行时注入

#### Scenario: 策略模块引用更新
- **WHEN** 策略文件加载完成
- **THEN** 引擎 SHALL 更新策略模块中的 `log` 和 `g` 引用，确保它们指向 `wealthdata` 模块中的最新实例
- **AND** 这确保即使策略在导入时获取了引用，也能使用正确的实例

#### Scenario: 无模块注入
- **WHEN** 引擎加载策略
- **THEN** 引擎 SHALL NOT 将函数注入到策略模块的命名空间
- **AND** 所有函数和对象都通过 `wealthdata` 模块提供
- **AND** 策略必须使用 `from wealthdata import *` 来访问这些功能

## MODIFIED Requirements

### Requirement: Context 线程局部存储

引擎 SHALL 管理 Context 对象在线程局部存储中的生命周期，以支持 wealthdata 兼容模块。

引擎 SHALL 管理 Context 对象在线程局部存储中的生命周期，以支持 wealthdata 兼容模块：

- **设置 Context**：在执行策略函数前，引擎 SHALL 将 Context 设置到线程局部存储
- **清理 Context**：在执行完成后（成功或失败），引擎 SHALL 清理线程局部存储中的 Context
- **线程安全**：每个执行线程 SHALL 有独立的 Context，支持并发策略执行
- **异常处理**：即使策略执行抛出异常，引擎 SHALL 确保 Context 被正确清理
- **策略模块清理**：在执行完成后，引擎 SHALL 清理线程局部存储中的策略模块引用

#### Scenario: Context 设置和清理
- **WHEN** 引擎开始执行策略函数
- **THEN** 引擎 SHALL 在执行前将 Context 设置到线程局部存储
- **AND** 在执行完成后（成功或失败），引擎 SHALL 清理线程局部存储中的 Context
- **AND** 引擎 SHALL 清理线程局部存储中的策略模块引用

#### Scenario: 异常情况下的清理
- **WHEN** 策略执行抛出异常
- **THEN** 引擎 SHALL 确保 Context 被正确清理（使用 finally 块）
- **AND** 引擎 SHALL 确保策略模块引用被正确清理

