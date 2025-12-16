# 行情数据规范

## 背景及目标

### 背景

行情数据是量化策略决策的基础，需要提供准确、完整的市场数据（K线、技术指标等）。通过标准化的行情数据结构，确保策略能够一致地访问不同来源、不同分辨率的市场数据。

### 目标

- **多分辨率支持**：支持 1m、3m、5m、15m、30m、1h、4h、1d、1w 等多种时间分辨率
- **完整 K 线数据**：提供 OHLCV（开盘价、最高价、最低价、收盘价、成交量）数据
- **技术指标支持**：内置 MA（移动平均）和 EMA（指数移动平均）指标
- **多品种支持**：支持同时传递多个品种、多个分辨率的行情数据
- **精度保证**：价格和成交量使用字符串类型，保证精度

## 使用场景/用户故事

### 场景 1：基于 K 线数据判断趋势

**用户故事**：策略需要根据 1 小时 K 线数据判断市场趋势，当价格突破均线时发出交易信号。

**流程**：
1. 策略从 `ExecRequest.market_data_context[]` 获取行情数据
2. 查找 `symbol = "BTCUSDT"` 且 `timeframe = "1h"` 的 `MarketDataContext`
3. 读取最新的 `Bar` 数据，获取收盘价
4. 读取对应的 `Indicator` 数据，获取 MA 指标
5. 比较收盘价和均线，判断趋势

### 场景 2：多时间周期分析

**用户故事**：策略需要同时分析 1 小时和 4 小时 K 线，进行多周期确认。

**流程**：
1. 策略获取多个 `MarketDataContext`，分别对应 1h 和 4h 分辨率
2. 分别分析两个时间周期的趋势
3. 当两个周期都显示同一趋势时，发出交易信号

### 场景 3：技术指标计算

**用户故事**：策略需要根据 MA 和 EMA 指标判断买卖点。

**流程**：
1. 策略从 `Indicator` 中获取 MA 和 EMA 指标
2. 比较不同周期的均线（如 MA5 和 MA20）
3. 当短期均线上穿长期均线时，发出买入信号

## 接口/数据结构定义

### K 线（Bar）

```protobuf
message Bar {
    int64 open_time = 1;      // 开盘时间（unix时间戳毫秒）
    int64 close_time = 2;     // 收盘时间（unix时间戳毫秒），未闭合时为当前计算窗口的结束时间
    string open = 3;          // 开盘价（字符串，保持精度）
    string high = 4;          // 最高价（字符串，保持精度）
    string low = 5;           // 最低价（字符串，保持精度）
    string close = 6;         // 收盘价（字符串，保持精度）
    string volume = 7;        // 成交量（字符串，保持精度）
}
```

### 技术指标（Indicator）

```protobuf
message Indicator {
    int64 timestamp = 1;              // 时间戳（unix毫秒时间戳）
    MAIndicator ma_indicator = 2;     // MA 指标
    EMAIndicator ema_indicator = 3;   // EMA指标
}
```

### MA 指标（MAIndicator）

```protobuf
message MAIndicator {
    map<int,double> moving_average = 1;  // 不同天数下的 MA（Moving Average）指标
}
```

### EMA 指标（EMAIndicator）

```protobuf
message EMAIndicator {
    map<int,double> exp_moving_average = 1;  // 不同天数下的 EMA（Exponential Moving Average）指标
}
```

### 行情上下文（MarketDataContext）

```protobuf
message MarketDataContext {
    string symbol = 1;                    // 交易对
    string timeframe = 2;                 // 分辨率（1m/3m/5m/15m/30m/1h/4h/1d/1w）
    repeated Bar bars = 3;                // 行情数据
    repeated Indicator indicators = 4;    // 技术指标数据，与每个 bar 的 close_time 对齐
}
```

## 约束与注意事项

### 时间分辨率

**支持的分辨率**：
- `1m`：1 分钟
- `3m`：3 分钟
- `5m`：5 分钟
- `15m`：15 分钟
- `30m`：30 分钟
- `1h`：1 小时
- `4h`：4 小时
- `1d`：1 天
- `1w`：1 周

**注意事项**：
- 分辨率字符串必须严格匹配上述格式（小写字母 + 数字）
- 不同交易所可能支持不同的分辨率，策略应检查可用性

### K 线数据

1. **时间字段**：
   - `open_time`：K 线的开始时间
   - `close_time`：K 线的结束时间
   - 对于未闭合的 K 线，`close_time` 为当前计算窗口的结束时间

2. **价格字段**：
   - 所有价格字段（`open`、`high`、`low`、`close`）使用字符串类型
   - 字符串格式保证精度，避免浮点数精度问题
   - 策略使用时应转换为 Decimal 或高精度数值类型进行计算

3. **成交量**：
   - `volume` 使用字符串类型，保证精度
   - 成交量单位为交易对的基准货币（如 BTCUSDT 的 volume 单位为 BTC）

4. **数据顺序**：
   - `bars[]` 数组按时间顺序排列，最早的 K 线在前，最新的在后
   - 最后一个元素为最新的 K 线（可能未闭合）

### 技术指标

1. **时间对齐**：
   - `indicators[]` 与 `bars[]` 按时间对齐
   - `Indicator.timestamp` 对应 `Bar.close_time`
   - 数组长度可能不同（指标计算需要历史数据）

2. **MA 指标**：
   - `moving_average` 为 map 类型，key 为周期（如 5、10、20、60）
   - value 为该周期的移动平均值
   - 例如：`moving_average[5]` 表示 5 周期移动平均

3. **EMA 指标**：
   - `exp_moving_average` 为 map 类型，key 为周期
   - value 为该周期的指数移动平均值
   - EMA 对近期价格赋予更高权重

4. **指标计算**：
   - 指标由系统计算并传递，策略不应自行计算
   - 如果某个周期的指标不可用，map 中可能不包含该 key

### 多分辨率支持

1. **同时传递**：`ExecRequest.market_data_context[]` 可以包含多个 `MarketDataContext`，每个对应不同的品种或分辨率

2. **数据一致性**：不同分辨率的 K 线数据应保持时间一致性，避免时间戳冲突

3. **数据量控制**：系统应控制传递的 K 线数量，避免数据过大影响性能

## 示例与用例

### 示例 1：读取最新 K 线数据

```python
# 查找目标品种和分辨率的行情数据
market_data = None
for ctx in exec_request.market_data_context:
    if ctx.symbol == "BTCUSDT" and ctx.timeframe == "1h":
        market_data = ctx
        break

if market_data and market_data.bars:
    # 获取最新的 K 线
    latest_bar = market_data.bars[-1]
    
    # 读取价格（转换为 Decimal 保证精度）
    from decimal import Decimal
    open_price = Decimal(latest_bar.open)
    high_price = Decimal(latest_bar.high)
    low_price = Decimal(latest_bar.low)
    close_price = Decimal(latest_bar.close)
    volume = Decimal(latest_bar.volume)
    
    print(f"最新 K 线: {latest_bar.open_time} - {latest_bar.close_time}")
    print(f"开盘: {open_price}, 最高: {high_price}, 最低: {low_price}, 收盘: {close_price}")
    print(f"成交量: {volume}")
```

### 示例 2：计算价格变化

```python
# 获取最新的两根 K 线
if len(market_data.bars) >= 2:
    latest_bar = market_data.bars[-1]
    previous_bar = market_data.bars[-2]
    
    latest_close = Decimal(latest_bar.close)
    previous_close = Decimal(previous_bar.close)
    
    # 计算涨跌幅
    price_change = latest_close - previous_close
    price_change_pct = (price_change / previous_close) * 100
    
    print(f"价格变化: {price_change} ({price_change_pct:.2f}%)")
```

### 示例 3：使用 MA 指标判断趋势

```python
# 获取技术指标
if market_data.indicators:
    latest_indicator = market_data.indicators[-1]
    
    if latest_indicator.ma_indicator:
        ma5 = latest_indicator.ma_indicator.moving_average.get(5)
        ma20 = latest_indicator.ma_indicator.moving_average.get(20)
        
        if ma5 and ma20:
            latest_close = Decimal(market_data.bars[-1].close)
            
            # 判断趋势
            if latest_close > ma5 > ma20:
                print("上升趋势：价格 > MA5 > MA20")
            elif latest_close < ma5 < ma20:
                print("下降趋势：价格 < MA5 < MA20")
```

### 示例 4：多周期分析

```python
# 获取 1h 和 4h 的行情数据
market_data_1h = None
market_data_4h = None

for ctx in exec_request.market_data_context:
    if ctx.symbol == "BTCUSDT":
        if ctx.timeframe == "1h":
            market_data_1h = ctx
        elif ctx.timeframe == "4h":
            market_data_4h = ctx

# 分析两个周期的趋势
if market_data_1h and market_data_4h:
    close_1h = Decimal(market_data_1h.bars[-1].close)
    close_4h = Decimal(market_data_4h.bars[-1].close)
    
    # 获取均线
    ma20_1h = market_data_1h.indicators[-1].ma_indicator.moving_average.get(20) if market_data_1h.indicators else None
    ma20_4h = market_data_4h.indicators[-1].ma_indicator.moving_average.get(20) if market_data_4h.indicators else None
    
    # 多周期确认
    if ma20_1h and ma20_4h:
        trend_1h = "上升" if close_1h > ma20_1h else "下降"
        trend_4h = "上升" if close_4h > ma20_4h else "下降"
        
        if trend_1h == trend_4h == "上升":
            print("多周期确认：上升趋势")
        elif trend_1h == trend_4h == "下降":
            print("多周期确认：下降趋势")
```

### 示例 5：使用 EMA 指标

```python
# 获取 EMA 指标
if market_data.indicators:
    latest_indicator = market_data.indicators[-1]
    
    if latest_indicator.ema_indicator:
        ema12 = latest_indicator.ema_indicator.exp_moving_average.get(12)
        ema26 = latest_indicator.ema_indicator.exp_moving_average.get(26)
        
        if ema12 and ema26:
            # MACD 策略：EMA12 上穿 EMA26 为买入信号
            if ema12 > ema26:
                print("EMA12 > EMA26，买入信号")
            else:
                print("EMA12 < EMA26，卖出信号")
```

## Q&A、FAQ

### Q1：为什么价格使用字符串类型？

**A**：使用字符串类型可以保证精度，避免浮点数精度问题。在金融计算中，精度非常重要，建议策略使用 Decimal 类型进行价格计算。

### Q2：如何判断 K 线是否闭合？

**A**：可以通过比较 `close_time` 和当前时间来判断。如果 `close_time` 小于当前时间，说明 K 线已闭合；如果 `close_time` 等于当前计算窗口的结束时间，说明 K 线可能未闭合。

### Q3：技术指标数据可能为空吗？

**A**：可能。如果历史数据不足，某些周期的指标可能无法计算。策略应检查指标是否存在，并提供默认处理逻辑。

### Q4：如何获取历史 K 线数据？

**A**：`bars[]` 数组包含历史 K 线数据，按时间顺序排列。策略可以通过数组索引访问历史数据，例如 `bars[-10]` 表示 10 根 K 线之前的数据。

### Q5：不同分辨率的 K 线数据如何对齐？

**A**：不同分辨率的 K 线数据在 `market_data_context[]` 中分别存储。策略需要根据 `symbol` 和 `timeframe` 查找对应的数据。系统保证同一品种的不同分辨率数据时间一致。

---

**相关文档**：
- [策略执行引擎规范](../strategy-engine/spec.md)
- [策略开发规范](../strategy-development/spec.md)
- [订单管理规范](../order/spec.md)

