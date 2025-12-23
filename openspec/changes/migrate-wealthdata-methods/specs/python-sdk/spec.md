## ADDED Requirements

### Requirement: wealthdata 数据访问方法

Python SDK SHALL 提供 wealthdata 数据访问方法，作为独立的数据访问接口，可在不同实现层（回测、模拟交易、实盘）复用。

#### Scenario: 获取价格数据
- **WHEN** 策略调用 `get_price(symbol, count, frequency)`
- **THEN** SDK SHALL 通过数据适配器获取历史 K 线数据
- **AND** 返回 pandas DataFrame，包含 open, high, low, close, volume 列
- **AND** 数据适配器由策略框架在执行前注册

#### Scenario: 获取 Bar 对象数据
- **WHEN** 策略调用 `get_bars(symbol, count, frequency)`
- **THEN** SDK SHALL 通过数据适配器获取历史 Bar 数据
- **AND** 返回 pandas DataFrame，格式与 get_price 一致
- **AND** 支持 JoinQuant 兼容的 unit 参数别名

#### Scenario: 获取所有证券信息
- **WHEN** 策略调用 `get_all_securities(types, date)`
- **THEN** SDK SHALL 通过数据适配器获取所有可用交易对信息
- **AND** 返回 pandas DataFrame，包含 display_name, name, start_date, end_date, type 列
- **AND** 优先级为 2（中等优先级）

#### Scenario: 获取交易日历
- **WHEN** 策略调用 `get_trade_days(start_date, end_date, count)`
- **THEN** SDK SHALL 通过数据适配器获取交易日列表
- **AND** 返回日期字符串列表（YYYY-MM-DD 格式）
- **AND** 加密货币市场返回所有日期（7x24 交易）
- **AND** 优先级为 2（中等优先级）

#### Scenario: 获取指数成分股
- **WHEN** 策略调用 `get_index_stocks(index_symbol, date)`
- **THEN** SDK SHALL 通过数据适配器或配置获取指数成分股列表
- **AND** 返回交易对符号列表
- **AND** 支持 BTC_INDEX, ETH_INDEX, DEFI_INDEX 等
- **AND** 优先级为 3（较低优先级）

#### Scenario: 获取指数权重
- **WHEN** 策略调用 `get_index_weights(index_symbol, date)`
- **THEN** SDK SHALL 通过数据适配器或配置获取指数权重
- **AND** 返回 pandas DataFrame，包含 code, weight 列
- **AND** 优先级为 3（较低优先级）

#### Scenario: 获取基本面数据
- **WHEN** 策略调用 `get_fundamentals(valuation, statDate, statDateCount)`
- **THEN** SDK SHALL 通过数据适配器获取基本面数据
- **AND** 返回 pandas DataFrame 或空 DataFrame（加密货币不适用时）
- **AND** 发出警告提示财务数据概念不完全适用于加密货币
- **AND** 优先级为 4（最低优先级）

#### Scenario: 获取行业分类
- **WHEN** 策略调用 `get_industry(security, date)`
- **THEN** SDK SHALL 通过数据适配器或配置获取行业分类
- **AND** 返回分类字符串（如 'Layer1', 'DeFi', 'Layer2' 等）
- **AND** 优先级为 4（最低优先级）

#### Scenario: 获取成交记录
- **WHEN** 策略调用 `get_trades()`
- **THEN** SDK SHALL 通过数据适配器获取已完成订单的成交记录
- **AND** 返回字典，键为订单 ID，值为成交记录字典
- **AND** 优先级为 1（高优先级）

#### Scenario: 数据适配器未注册
- **WHEN** SDK 方法被调用但数据适配器未注册
- **THEN** SDK SHALL 抛出 RuntimeError，提示适配器未注册
- **AND** 错误信息应明确指出需要由策略框架注册适配器

#### Scenario: SDK 方法独立使用
- **WHEN** SDK 方法在策略执行引擎外部被调用
- **THEN** SDK SHALL 支持独立使用，通过手动注册数据适配器
- **AND** 允许在测试、脚本等场景下使用 SDK 方法

### Requirement: 数据适配器接口

Python SDK SHALL 定义数据适配器接口，允许不同实现层提供数据源。

#### Scenario: 适配器接口定义
- **WHEN** 实现层需要提供数据源
- **THEN** 实现层 SHALL 实现 DataAdapter 接口
- **AND** 接口 SHALL 包含获取历史数据、证券信息、指数信息等方法
- **AND** 接口 SHALL 支持线程安全的注册和获取

#### Scenario: 适配器注册
- **WHEN** 策略框架开始执行策略
- **THEN** 策略框架 SHALL 注册数据适配器到线程局部存储
- **AND** 适配器 SHALL 从 ExecRequest 的 market_data_context 获取数据
- **AND** 适配器 SHALL 在策略执行完成后自动清理

