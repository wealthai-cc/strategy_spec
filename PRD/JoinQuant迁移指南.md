# JoinQuant 迁移指南

> 本指南帮助 JoinQuant 用户将策略代码迁移到 WealthAI 策略框架，实现零代码修改的平滑迁移。

## 快速开始

### 迁移步骤

只需 **3 步**即可完成迁移：

1. **复制策略代码**：将 JoinQuant 策略代码复制到本地
2. **修改 import 语句**：将 `import jqdatasdk` 改为 `import wealthdata`
3. **调整交易品种格式**：将股票代码（如 `'000001.XSHE'`）改为交易对格式（如 `'BTCUSDT'`）

### 示例对比

#### JoinQuant 原始代码

```python
import jqdatasdk

def initialize(context):
    context.symbol = '000001.XSHE'  # 股票代码
    context.ma_period = 20

def handle_bar(context, bar):
    # 使用 jqdatasdk 获取数据
    df = jqdatasdk.get_price(context.symbol, count=context.ma_period, frequency='1d')
    ma = df['close'].mean()
    
    if bar.close > ma:
        order_buy(context.symbol, 100)  # 买入 100 股
```

#### 迁移后的代码

```python
import wealthdata  # 只改了这一行！

def initialize(context):
    context.symbol = 'BTCUSDT'  # 改为交易对格式
    context.ma_period = 20

def handle_bar(context, bar):
    # 代码完全不变！
    df = wealthdata.get_price(context.symbol, count=context.ma_period, frequency='1h')
    ma = df['close'].mean()
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)  # 改为 context.order_buy()
```

**变更总结**：
- ✅ Import 语句：`jqdatasdk` → `wealthdata`（1 行）
- ✅ 交易品种格式：股票代码 → 交易对（1 行）
- ✅ 下单 API：`order_buy()` → `context.order_buy()`（框架要求）
- ✅ **业务逻辑代码：完全不变！**

## API 兼容性

### 完全兼容的 API

以下 API 与 jqdatasdk 完全兼容，可以直接使用：

#### get_price()

```python
df = wealthdata.get_price(
    symbol='BTCUSDT',
    count=20,
    frequency='1h',
    end_date=None,  # 可选，受限于 ExecRequest 数据范围
    fields=None,    # 可选，默认返回所有字段
    skip_paused=False,  # 忽略（加密货币不适用）
    fq='pre'       # 忽略（加密货币不适用）
)
```

**返回格式**：pandas DataFrame，包含以下列：
- `open`：开盘价
- `high`：最高价
- `low`：最低价
- `close`：收盘价
- `volume`：成交量

**索引**：时间戳（Bar 的 close_time）

#### get_bars()

```python
df = wealthdata.get_bars(
    symbol='BTCUSDT',
    count=20,
    frequency='1h'  # 或使用 unit='1h'（JoinQuant 兼容）
)
```

功能与 `get_price()` 相同。支持 `unit` 参数作为 `frequency` 的别名（JoinQuant 兼容）。

#### get_all_securities()

```python
df = wealthdata.get_all_securities(
    types=None,  # 可选，忽略（加密货币不适用）
    date=None    # 可选，忽略（使用当前上下文数据）
)
```

**返回格式**：pandas DataFrame，包含以下列：
- `display_name`：交易对显示名称（与 name 相同）
- `name`：交易对符号（DataFrame 索引）
- `start_date`：不适用（None）
- `end_date`：不适用（None，表示仍在交易）
- `type`：'crypto'（所有都是加密货币交易对）

**数据来源**：从 `ExecRequest.market_data_context` 中提取所有唯一的交易对符号

#### get_trade_days()

```python
days = wealthdata.get_trade_days(
    start_date='2025-01-01',  # 可选，开始日期
    end_date='2025-01-31',    # 可选，结束日期
    count=30                   # 可选，返回最近 N 天
)
```

**返回格式**：日期字符串列表（'YYYY-MM-DD' 格式），按时间顺序排列（从早到晚）

**注意**：
- **加密货币市场**：7x24 交易，返回所有日期（包括周末）
- **股票市场**：返回实际交易日（排除周末和节假日）
- 市场类型自动识别（通过标的代码格式）

#### get_index_stocks()

```python
stocks = wealthdata.get_index_stocks(
    index_symbol='BTC_INDEX',  # 指数标识符
    date=None                   # 可选，忽略（返回当前成分）
)
```

**返回格式**：交易对符号列表（如 `['BTCUSDT', 'ETHUSDT', ...]`）

**支持的指数**：
- `BTC_INDEX` - BTC 指数
- `ETH_INDEX` - ETH 指数
- `DEFI_INDEX` - DeFi 指数
- `LAYER1_INDEX` - Layer1 指数
- `LAYER2_INDEX` - Layer2 指数

#### get_index_weights()

```python
df = wealthdata.get_index_weights(
    index_symbol='BTC_INDEX',  # 指数标识符
    date=None                   # 可选，忽略（返回当前权重）
)
```

**返回格式**：pandas DataFrame，包含以下列：
- `code`：交易对符号（DataFrame 索引）
- `weight`：权重（0.0 到 1.0 之间）

#### get_fundamentals()

```python
df = wealthdata.get_fundamentals(
    valuation={'code': 'BTCUSDT'},  # 简化的查询对象（dict 或 None）
    statDate=None,                   # 可选，忽略
    statDateCount=None               # 可选，忽略
)
```

**返回格式**：pandas DataFrame，包含基本交易对信息（如果可用）或空 DataFrame

**注意**：财务数据概念不完全适用于加密货币，此函数会发出警告并返回有限数据

#### get_trades()

```python
trades = wealthdata.get_trades()
```

**返回格式**：字典，键为订单 ID，值为成交记录字典，包含：
- `security`：交易对符号
- `price`：成交价格
- `amount`：成交数量
- `time`：成交时间
- `order_id`：订单 ID

**使用示例**：
```python
def after_market_close(context):
    trades = wealthdata.get_trades()
    for order_id, trade in trades.items():
        log.info(f"成交: {trade['security']} @ {trade['price']}, 数量: {trade['amount']}")
```

#### get_industry()

```python
category = wealthdata.get_industry(
    security='BTCUSDT',  # 交易对符号
    date=None            # 可选，忽略（返回当前分类）
)
```

**返回格式**：分类字符串（如 'Layer1', 'DeFi', 'Layer2', 'Exchange' 等）

**支持的分类**：
- `Layer1` - 第一层区块链（BTC, ETH, SOL 等）
- `Layer2` - 第二层解决方案（MATIC, ARB, OP 等）
- `DeFi` - 去中心化金融（UNI, AAVE, LINK 等）
- `Exchange` - 交易所代币（BNB, FTT 等）
- `Meme` - 模因币（DOGE, SHIB 等）
- `Gaming` - 游戏/Metaverse（AXS, SAND 等）
- `Storage` - 存储（FIL, AR 等）

### 数据格式对比

| 维度 | JoinQuant jqdatasdk | WealthAI wealthdata | 兼容性 |
|------|---------------------|---------------------|--------|
| 返回类型 | pandas DataFrame | pandas DataFrame | ✅ 完全一致 |
| 列名 | open, high, low, close, volume | open, high, low, close, volume | ✅ 完全一致 |
| 索引 | 时间戳 | 时间戳 | ✅ 完全一致 |
| 数据类型 | float | float | ✅ 完全一致 |

## 主要差异说明

### 1. 数据范围限制

**JoinQuant**：
- 可以查询任意历史数据
- 数据来自实时数据库

**WealthAI**：
- 数据范围受限于 `ExecRequest.market_data_context`
- 只能访问策略执行时传入的数据快照

**影响**：
- 如果请求的数据超出可用范围，会返回警告但不会报错
- 建议在策略中检查返回的 DataFrame 长度

**示例**：
```python
df = wealthdata.get_price('BTCUSDT', count=100, frequency='1h')
if len(df) < 100:
    # 数据不足，可能需要调整策略逻辑
    print(f"Warning: Only {len(df)} bars available, requested 100")
```

### 2. 交易品种格式

**JoinQuant**：使用股票代码格式
- `'000001.XSHE'` - 深交所股票
- `'600000.XSHG'` - 上交所股票

**WealthAI**：使用交易对格式
- `'BTCUSDT'` - BTC/USDT 交易对
- `'ETHUSDT'` - ETH/USDT 交易对

### 3. 下单 API

**JoinQuant**：
```python
order_buy(context.symbol, 100)  # 买入 100 股
order_sell(context.symbol, 100)  # 卖出 100 股
```

**WealthAI**：
```python
context.order_buy(context.symbol, 0.1, price=50000.0)  # 买入 0.1 BTC，限价 50000
context.order_sell(context.symbol, 0.1)  # 卖出 0.1 BTC，市价
```

**主要差异**：
- 需要调用 `context.order_buy()` 而不是 `order_buy()`
- 数量单位：股票用"股"，加密货币用"币"（如 0.1 BTC）
- 支持限价和市价单（通过 `price` 参数）

### 4. 时间分辨率格式

**JoinQuant**：
- `'daily'` - 日线
- `'1d'` - 日线
- `'1h'` - 小时线

**WealthAI**：
- `'1d'` - 日线
- `'1h'` - 小时线
- `'1m'`, `'5m'`, `'15m'`, `'30m'`, `'4h'`, `'1w'` - 支持多种分辨率

**注意**：`'daily'` 需要改为 `'1d'`

## 迁移检查清单

### 代码修改

- [ ] 将 `import jqdatasdk` 或 `import jqdata` 改为 `import wealthdata`
- [ ] 将股票代码改为交易对格式（如 `'000001.XSHE'` → `'BTCUSDT'`）
- [ ] 将 `order_buy()` 改为 `context.order_buy()` 或使用 `order_value()` / `order_target()`
- [ ] 将 `order_sell()` 改为 `context.order_sell()` 或使用 `order_target()`
- [ ] 将 `'daily'` 改为 `'1d'`（如果使用）
- [ ] 检查数量单位（股 → 币，如 100 → 0.1）
- [ ] 如果使用 `get_bars()` 的 `unit` 参数，可以保持不变（已兼容）
- [ ] 如果使用 `g` 全局变量，无需修改（自动注入）
- [ ] 如果使用 `log` 模块，无需修改（自动注入）
- [ ] 如果使用 `run_daily()`，无需修改（自动注入）

### 代码验证

- [ ] 验证 `wealthdata.get_price()` 调用正常
- [ ] 验证 DataFrame 操作正常（mean, std 等）
- [ ] 验证下单操作正常
- [ ] 运行测试策略验证功能

## 常见问题

### Q1：为什么需要修改下单 API？

**A**：WealthAI 框架要求通过 `context` 对象进行下单操作，这是框架设计的一部分。`context.order_buy()` 会收集订单操作，由引擎统一处理。

### Q2：数据范围限制会影响策略吗？

**A**：取决于策略的数据需求。如果策略只需要最近的数据（如最近 20-50 根 K 线），通常不会有问题。如果需要很长的历史数据，可能需要调整策略逻辑或确保 ExecRequest 中包含足够的数据。

### Q3：pandas DataFrame 操作是否完全兼容？

**A**：是的。`wealthdata.get_price()` 返回的 DataFrame 格式与 jqdatasdk 完全一致，所有 pandas 操作（mean, std, rolling 等）都可以直接使用。

### Q4：是否支持所有 jqdatasdk API？

**A**：目前支持以下 API：
- ✅ `get_price()` - 完全支持
- ✅ `get_bars()` - 完全支持
- ✅ `get_all_securities()` - 完全支持（从 market_data_context 提取）
- ✅ `get_trade_days()` - 完全支持（适配 7x24 交易）
- ✅ `get_index_stocks()` - 完全支持（加密货币指数）
- ✅ `get_index_weights()` - 完全支持（指数权重）
- ⚠️ `get_fundamentals()` - 简化支持（返回基本交易对信息，有警告）
- ✅ `get_industry()` - 完全支持（加密货币分类）

### Q5：如何测试迁移后的策略？

**A**：可以使用框架提供的测试脚本：

```bash
python3 test_strategy.py your_strategy.py
```

## 完整迁移示例

### 基础迁移示例
查看 `strategy/joinquant_migration_example.py` 获取基础的迁移示例代码。

### 新 API 使用示例

#### 指数跟踪策略
查看 `strategy/index_based_strategy.py` - 使用 `get_index_stocks()` 和 `get_index_weights()` 构建指数跟踪策略

#### 行业轮动策略
查看 `strategy/industry_rotation_strategy.py` - 使用 `get_all_securities()` 和 `get_industry()` 构建行业轮动策略

#### 综合 API 示例
查看 `strategy/comprehensive_jqdata_example.py` - 展示所有 wealthdata API 的使用方法

## 获取帮助

如有问题，请：
1. 查看 [策略开发规范](../openspec/specs/strategy-development/spec.md)
2. 查看 [策略开发快速开始](./策略开发快速开始.md)
3. 查看示例代码：`strategy/joinquant_migration_example.py`

---

**最后更新**：2025-12-16  
**版本**：2.0（新增 6 个 API 支持：get_all_securities, get_trade_days, get_index_stocks, get_index_weights, get_fundamentals, get_industry）

