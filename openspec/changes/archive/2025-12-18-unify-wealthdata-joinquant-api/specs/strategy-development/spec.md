## MODIFIED Requirements

### Requirement: wealthdata 兼容模块（JoinQuant 兼容）

策略 SHALL 使用 `wealthdata` 模块进行数据访问，提供与 JoinQuant jqdatasdk 兼容的接口。

**所有 JoinQuant 兼容的 API SHALL 在 `wealthdata` 模块中定义，策略 SHALL 通过 `from wealthdata import *` 访问所有功能。**

**价格数据 API**：
- `wealthdata.get_price(symbol, count=None, end_date=None, frequency='1h', ...)`：获取价格数据
  - 返回：pandas DataFrame，包含 open, high, low, close, volume 列
  - 与 jqdatasdk.get_price() 接口完全一致
  - 内部映射到 `context.history()` 方法
- `wealthdata.get_bars(symbol, count=None, end_date=None, frequency='1h', ...)`：获取 K 线数据
  - 与 `get_price()` 功能相同，返回格式一致
  - 支持 `unit` 参数（作为 `frequency` 的别名）

**证券信息 API**：
- `wealthdata.get_all_securities(types=None, date=None)`：获取所有交易对信息
  - 返回：pandas DataFrame，包含 display_name, name, start_date, end_date, type 列
  - 从 market_data_context 提取所有唯一交易对
- `wealthdata.get_trade_days(start_date=None, end_date=None, count=None)`：获取交易日列表
  - 返回：日期字符串列表（'YYYY-MM-DD' 格式）
  - 加密货币 7x24 交易，返回所有日期（包括周末）
- `wealthdata.get_index_stocks(index_symbol, date=None)`：获取指数成分
  - 返回：交易对符号列表
  - 支持 BTC_INDEX, ETH_INDEX, DEFI_INDEX 等
- `wealthdata.get_index_weights(index_symbol, date=None)`：获取指数权重
  - 返回：pandas DataFrame，包含 code, weight 列
- `wealthdata.get_fundamentals(valuation, statDate=None, statDateCount=None)`：获取财务数据
  - 返回：pandas DataFrame（简化适配，返回基本交易对信息或空 DataFrame）
  - 注意：财务数据概念不完全适用于加密货币，会发出警告
- `wealthdata.get_industry(security, date=None)`：获取行业分类
  - 返回：分类字符串（如 'Layer1', 'DeFi', 'Layer2' 等）
- `wealthdata.get_trades()`：获取成交记录
  - 返回：字典，键为订单 ID，值为成交记录字典

**策略函数 API**：
- `log`：日志对象，支持 `info()`, `warn()`, `error()`, `debug()`, `set_level()` 方法
- `g`：全局变量对象，用于存储策略状态
- `run_daily(func, time='open', reference_security=None)`：注册定时运行函数
- `order_value(symbol, value, price=None)`：按金额下单
- `order_target(symbol, target_qty, price=None)`：目标持仓下单

**配置函数 API**：
- `set_benchmark(security)`：设置基准
- `set_option(key, value)`：设置选项
- `set_order_cost(cost, type='stock')`：设置订单成本
- `OrderCost`：订单成本配置类

#### Scenario: 策略导入所有 JoinQuant API
- **WHEN** 策略执行 `from wealthdata import *`
- **THEN** 所有 JoinQuant 兼容的 API 都可用，包括数据访问函数、策略函数和配置函数
- **AND** 所有函数和对象都来自 `wealthdata` 模块，无需运行时注入

#### Scenario: 日志输出可见性
- **WHEN** 策略调用 `log.info()`, `log.debug()`, `log.warn()`, 或 `log.error()`
- **THEN** 日志输出必须可见，出现在策略执行的输出中
- **AND** 日志格式为 `[LEVEL] message`，其中 LEVEL 为 INFO、DEBUG、WARN 或 ERROR

#### Scenario: 策略隔离
- **WHEN** 多个策略并发执行
- **THEN** 每个策略有自己独立的 `g` 和 `log` 对象实例
- **AND** 策略之间的状态不会相互干扰

#### Scenario: 无需运行时注入
- **WHEN** 策略使用 `from wealthdata import *`
- **THEN** 所有函数和对象都可用，无需引擎进行运行时注入
- **AND** 策略模块中不需要额外的导入语句

**注意事项**：
- `wealthdata` 模块通过线程局部存储访问当前执行的 Context
- 数据范围受限于 ExecRequest 中的 market_data_context
- 返回 pandas DataFrame 格式，兼容现有 pandas 分析代码
- 支持零代码修改迁移（只需修改 import 语句）
- 指数和分类数据来自静态配置，可通过配置文件扩展

