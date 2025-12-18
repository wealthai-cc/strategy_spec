# Strategy Testing Specification Delta

## ADDED Requirements

### Requirement: K线测试数据生成
策略测试工具 SHALL 生成真实的K线测试数据，用于策略回测和验证。

#### Scenario: 生成高波动K线数据
- **WHEN** 策略测试工具生成K线数据
- **THEN** K线数据 SHALL 具有较大的波动幅度（至少是基础波动率的5-8倍，根据市场类型调整）
- **AND** K线数据 SHALL 包含价格跳空（开盘价与前一根K线收盘价的差异，概率20-30%）
- **AND** K线数据 SHALL 包含连续涨跌模式（模拟市场情绪，60-70%概率延续前一根K线方向）
- **AND** K线数据 SHALL 包含震荡区间模式（价格在一定区间内震荡，模拟横盘整理）

#### Scenario: 真实的OHLC关系
- **WHEN** 生成K线数据
- **THEN** 每根K线的OHLC关系 SHALL 符合真实市场特征：
  - `high >= max(open, close)`（最高价至少是开盘价和收盘价的最大值）
  - `low <= min(open, close)`（最低价至少是开盘价和收盘价的最小值）
  - 包含上影线和下影线（high和low与open/close的差异）
  - 上影线和下影线的长度符合真实市场特征（通常为实体长度的0.3-0.8倍）

#### Scenario: 成交量与价格波动关联
- **WHEN** 生成K线数据
- **THEN** 成交量 SHALL 与价格波动强相关：
  - 价格波动越大，成交量越大
  - 涨跌幅越大，成交量越大
  - 价格在高位或低位时，成交量可能增加（模拟关键位置交易活跃）

#### Scenario: 不同市场类型的波动特征
- **WHEN** 生成不同市场类型的K线数据
- **THEN** 波动幅度 SHALL 根据市场类型调整：
  - A股：波动倍数为5倍（基础波动率 × 5）
  - 美股：波动倍数为4倍
  - 港股：波动倍数为4倍
  - 加密货币：波动倍数为8倍

### Requirement: 完整回测执行
策略测试工具 SHALL 执行完整的逐K线回测，确保策略在整个回测周期内都能根据条件产生买卖点。

#### Scenario: 使用BacktestEngine执行回测
- **WHEN** 策略使用 `run_daily` 注册定时函数
- **THEN** 测试工具 SHALL 使用 `BacktestEngine.run_backtest()` 执行完整回测
- **AND** 回测 SHALL 遍历每根K线，在每根K线上调用 `before_market_open` 和 `market_open`
- **AND** 账户状态（现金、持仓）SHALL 在每根K线之间正确更新
- **AND** 订单 SHALL 在整个回测周期内分布，而不是集中在最后

#### Scenario: 收集整个回测周期的订单
- **WHEN** 执行完整回测
- **THEN** 测试工具 SHALL 收集整个回测周期内的所有订单
- **AND** 每个订单的时间戳 SHALL 正确对应到对应的K线
- **AND** 订单 SHALL 按照时间顺序排列

#### Scenario: 验证策略执行逻辑
- **WHEN** 策略在整个回测周期内执行
- **THEN** 策略 SHALL 在每根K线上根据条件判断是否产生买卖点
- **AND** 如果条件满足，策略 SHALL 生成对应的订单
- **AND** 如果条件不满足，策略 SHALL 不生成订单（或生成其他类型的订单）

