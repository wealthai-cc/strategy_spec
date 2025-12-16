# JoinQuant 迁移指南 - 完整 API 列表

> 本文档列出所有支持的 JoinQuant 兼容 API 及其使用方法。

## 版本信息

**当前版本**: 2.0  
**更新日期**: 2025-01-XX  
**支持的 JoinQuant API**: 8 个核心 API + 6 个兼容功能

## 数据查询 API

### 1. get_price()

获取价格数据，返回 pandas DataFrame。

```python
df = wealthdata.get_price(
    symbol='BTCUSDT',
    count=20,
    frequency='1h',
    end_date=None,
    fields=None,
    skip_paused=False,
    fq='pre'
)
```

**参数**：
- `symbol`: 交易对符号
- `count`: 获取的 K 线数量
- `frequency`: 时间分辨率（'1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'）
- `end_date`: 结束日期（可选，受限于 ExecRequest 数据范围）
- `fields`: 数据字段（可选，默认返回所有字段）
- `skip_paused`: 忽略（加密货币不适用）
- `fq`: 忽略（加密货币不适用）

**返回**: pandas DataFrame，包含 `open`, `high`, `low`, `close`, `volume` 列

### 2. get_bars()

获取 K 线数据，功能与 `get_price()` 相同。

```python
df = wealthdata.get_bars(
    symbol='BTCUSDT',
    count=20,
    frequency='1h',  # 或使用 unit='1h'（JoinQuant 兼容）
    unit=None,       # JoinQuant 兼容：frequency 的别名
    fields=None,
    skip_paused=False,
    fq='pre'
)
```

**新增**: 支持 `unit` 参数（作为 `frequency` 的别名）

### 3. get_all_securities()

获取所有可用交易对。

```python
df = wealthdata.get_all_securities(
    types=None,
    date=None
)
```

**返回**: pandas DataFrame，包含所有交易对信息

### 4. get_trade_days()

获取交易日列表。

```python
days = wealthdata.get_trade_days(
    start_date='2025-01-01',
    end_date='2025-01-31',
    count=30
)
```

**市场类型适配**：
- **股票市场**：返回实际交易日（排除周末和节假日）
- **加密货币市场**：返回所有日期（每天都是交易日）

### 5. get_index_stocks()

获取指数成分。

```python
stocks = wealthdata.get_index_stocks(
    index_symbol='BTC_INDEX',
    date=None
)
```

**返回**: 交易对符号列表

### 6. get_index_weights()

获取指数权重。

```python
df = wealthdata.get_index_weights(
    index_symbol='BTC_INDEX',
    date=None
)
```

**返回**: pandas DataFrame，包含成分和权重

### 7. get_fundamentals()

获取财务数据（简化实现）。

```python
df = wealthdata.get_fundamentals(
    valuation={'code': 'BTCUSDT'},
    statDate=None,
    statDateCount=None
)
```

**注意**: 加密货币不适用财务数据概念，返回有限数据

### 8. get_industry()

获取行业分类。

```python
category = wealthdata.get_industry(
    security='BTCUSDT',
    date=None
)
```

**返回**: 行业/分类字符串（如 'Layer1', 'DeFi'）

### 9. get_trades()

获取成交记录。

```python
trades = wealthdata.get_trades()
```

**返回**: 字典，键为订单 ID，值为成交记录

## 兼容功能

### 全局变量（g）

```python
# 无需导入，自动注入
g.security = 'BTCUSDT'
g.ma_period = 20
```

### 日志模块（log）

```python
# 无需导入，自动注入
log.info('信息')
log.warn('警告')
log.error('错误')
log.debug('调试')
log.set_level('order', 'error')
```

### 定时运行（run_daily）

```python
# 无需导入，自动注入
run_daily(before_market_open, time='before_open', reference_security='BTCUSDT')
run_daily(market_open, time='open', reference_security='BTCUSDT')
run_daily(after_market_close, time='after_close', reference_security='BTCUSDT')
```

**时间点**：
- `before_open`: 开盘前
- `open`: 开盘时
- `after_close`: 收盘后

### 下单函数

```python
# 无需导入，自动注入
order_value('BTCUSDT', 1000)  # 按金额下单
order_target('BTCUSDT', 0.5)  # 目标持仓下单
```

### 配置函数

```python
# 无需导入，自动注入
set_benchmark('BTCUSDT')
set_option('use_real_price', True)
set_order_cost(OrderCost(...), type='stock')
```

## Context 属性

### 时间属性

```python
context.current_dt  # datetime 对象，当前时间
```

### Portfolio 属性

```python
context.portfolio.available_cash      # 可用现金
context.portfolio.positions_value     # 持仓市值
context.portfolio.positions           # 字典式持仓访问
context.portfolio.positions['BTCUSDT'] # 获取特定持仓
```

## 市场类型支持

### 股票市场

- **A股**: `000001.XSHE`, `600000.XSHG`
- **美股**: `AAPL.US`
- **港股**: `00700.HK`

**特性**：
- 实际交易时间（A股 9:30-15:00）
- 交易日概念（排除周末和节假日）
- 数量为整数（股）

### 加密货币市场

- **交易对格式**: `BTCUSDT`, `ETHUSDT`

**特性**：
- 7x24 交易（每天都是交易日）
- 逻辑时间点（如 00:00）
- 支持小数数量

## 迁移示例

### 完整迁移示例

参考 `strategy/double_mean_migrated.py` 查看完整的迁移示例。

### 主要修改点

1. `import jqdata` → `import wealthdata`
2. 股票代码 → 交易对格式
3. `order_buy()` → `context.order_buy()` 或 `order_value()`
4. `get_bars(..., unit='1d')` → `get_bars(..., frequency='1d')` 或保持 `unit='1d'`（已兼容）

### 无需修改的部分

- `g` 全局变量（自动注入）
- `log` 日志模块（自动注入）
- `run_daily()` 定时运行（自动注入）
- `order_value()`, `order_target()`（自动注入）
- `set_benchmark()`, `set_option()`, `set_order_cost()`（自动注入）

## 版本历史

### v2.0 (2025-01-XX)

- ✅ 新增 `get_trades()` API
- ✅ 新增 `get_trade_days()` 市场类型适配
- ✅ 新增 `get_bars()` 的 `unit` 参数兼容
- ✅ 新增全局变量（g）支持
- ✅ 新增日志模块（log）支持
- ✅ 新增定时运行（run_daily）支持
- ✅ 新增下单函数（order_value, order_target）
- ✅ 新增配置函数（set_benchmark, set_option, set_order_cost）
- ✅ 扩展 Context 属性（current_dt, available_cash, positions_value, positions 字典）

### v1.0 (2024-XX-XX)

- ✅ 基础 API：`get_price()`, `get_bars()`
- ✅ 扩展 API：`get_all_securities()`, `get_index_stocks()`, `get_index_weights()`, `get_fundamentals()`, `get_industry()`

