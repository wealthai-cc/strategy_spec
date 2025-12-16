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
    frequency='1h'
)
```

功能与 `get_price()` 相同。

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

- [ ] 将 `import jqdatasdk` 改为 `import wealthdata`
- [ ] 将股票代码改为交易对格式（如 `'000001.XSHE'` → `'BTCUSDT'`）
- [ ] 将 `order_buy()` 改为 `context.order_buy()`
- [ ] 将 `order_sell()` 改为 `context.order_sell()`
- [ ] 将 `'daily'` 改为 `'1d'`（如果使用）
- [ ] 检查数量单位（股 → 币，如 100 → 0.1）

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

**A**：目前支持最常用的 API：
- ✅ `get_price()` - 完全支持
- ✅ `get_bars()` - 完全支持
- ⚠️ `get_fundamentals()` - 暂不支持（计划中）
- ⚠️ `get_trade_days()` - 暂不支持
- ⚠️ `get_all_securities()` - 暂不支持

### Q5：如何测试迁移后的策略？

**A**：可以使用框架提供的测试脚本：

```bash
python3 test_strategy.py your_strategy.py
```

## 完整迁移示例

查看 `strategy/joinquant_migration_example.py` 获取完整的迁移示例代码。

## 获取帮助

如有问题，请：
1. 查看 [策略开发规范](../openspec/specs/strategy-development/spec.md)
2. 查看 [策略开发快速开始](./策略开发快速开始.md)
3. 查看示例代码：`strategy/joinquant_migration_example.py`

---

**最后更新**：2025-12-16  
**版本**：1.0

