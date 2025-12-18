# Design: 增强 JoinQuant 兼容性

## Context

JoinQuant 是一个成熟的量化交易平台，拥有大量用户和策略代码。为了吸引这些用户迁移到我们的平台，需要提供高度的 API 兼容性。通过分析真实的 JoinQuant 策略代码（`double_mean.py`），我们发现了多个不兼容点，需要逐一解决。

**重要背景**：我们的策略框架需要同时支持股票市场（美股、港股、A股）和加密货币市场。股票市场与 JoinQuant 保持一致，加密货币市场需要根据 7x24 交易、无开盘收盘等特性进行调整。

## Goals / Non-Goals

### Goals

1. **最小化迁移成本**：让 JoinQuant 用户能够以最小修改迁移策略代码
2. **API 兼容性**：支持 JoinQuant 最常用的 API 和功能
3. **行为一致性**：
   - **股票市场**：API 行为和返回值与 JoinQuant 完全一致
   - **加密货币市场**：根据市场特性调整（7x24 交易、无开盘收盘等）
4. **向后兼容**：新增功能不影响现有策略代码
5. **市场类型自适应**：框架能够识别市场类型并应用相应的处理逻辑

### Non-Goals

1. **100% 兼容**：不追求完全兼容所有 JoinQuant API，只支持最常用的
2. **性能优化**：兼容性优先，性能优化可以后续进行
3. **复杂功能**：不实现 JoinQuant 的高级功能（如回测优化、因子分析等）

## Decisions

### Decision 1: 市场类型识别机制

**选择**：通过标的代码格式识别市场类型，股票使用 JoinQuant 格式（如 `000001.XSHE`），加密货币使用交易对格式（如 `BTCUSDT`）。

**理由**：
- 简单直接，不需要额外的配置
- 符合用户的使用习惯
- 可以快速判断市场类型

**实现方式**：
```python
def is_stock_market(symbol: str) -> bool:
    """判断是否为股票市场"""
    # JoinQuant 格式：代码.交易所后缀
    # 例如：000001.XSHE (A股), AAPL.US (美股), 00700.HK (港股)
    return '.' in symbol and not symbol.endswith('USDT')

def is_crypto_market(symbol: str) -> bool:
    """判断是否为加密货币市场"""
    # 加密货币格式：交易对（如 BTCUSDT, ETHUSDT）
    return not is_stock_market(symbol)
```

**市场类型映射**：
- **A股**：`XXXXXX.XSHE` (深交所) 或 `XXXXXX.XSHG` (上交所)
- **美股**：`XXXX.US` (如 `AAPL.US`)
- **港股**：`XXXXX.HK` (如 `00700.HK`)
- **加密货币**：交易对格式（如 `BTCUSDT`, `ETHUSDT`）

**边界情况处理**：
- **格式不规范**：如果标的代码格式无法识别（如 `BTC.USDT`），默认识别为加密货币市场
- **显式指定**：支持通过 `context.exchange` 或策略参数显式指定市场类型（优先级高于格式识别）
- **回退机制**：如果市场类型识别失败，记录警告并使用默认行为（加密货币市场）

**实现细节**：
```python
def detect_market_type(symbol: str, context: Optional[Context] = None) -> str:
    """检测市场类型"""
    # 1. 优先使用显式配置
    if context and hasattr(context, 'market_type'):
        return context.market_type
    
    # 2. 通过标的代码格式识别
    if '.' in symbol:
        suffix = symbol.split('.')[-1]
        if suffix in ['XSHE', 'XSHG']:
            return 'A_STOCK'
        elif suffix == 'US':
            return 'US_STOCK'
        elif suffix == 'HK':
            return 'HK_STOCK'
        elif suffix == 'USDT':
            # 可能是格式错误的加密货币，如 BTC.USDT
            return 'CRYPTO'
    
    # 3. 默认识别为加密货币
    return 'CRYPTO'
```

### Decision 2: 定时运行机制（run_daily）

**选择**：在引擎层面实现定时函数注册和调用，在 `before_trading` 生命周期中检查并调用注册的函数。根据市场类型调整时间匹配逻辑。

**理由**：
- 不需要修改 gRPC 协议（`ExecRequest`）
- 实现简单，成本低
- 可以根据市场类型灵活调整

**实现方式**：
```python
# 在策略文件中注册定时函数
run_daily(before_market_open, time='before_open', reference_security='000001.XSHE')  # 股票
run_daily(before_market_open, time='before_open', reference_security='BTCUSDT')      # 加密货币

# 引擎在 before_trading 中检查时间并调用
# 根据市场类型匹配时间：
# - 股票市场：匹配实际开盘时间（如 9:30）
# - 加密货币市场：匹配配置的起始时间（如 00:00）
```

**市场类型适配**：
- **股票市场**（与 JoinQuant 一致）：
  - `before_open`: 交易日开盘前（A股 9:25，美股/港股根据时区）
  - `open`: 交易日开盘时（A股 9:30，美股/港股根据时区）
  - `after_close`: 交易日收盘后（A股 15:05，美股/港股根据时区）
  - 只在交易日触发（跳过节假日）
- **加密货币市场**（7x24 交易）：
  - `before_open`: 每天 00:00（或配置的起始时间，逻辑性概念）
  - `open`: 每天 00:00（或配置的起始时间，逻辑性概念）
  - `after_close`: 每天 23:59（或配置的结束时间，逻辑性概念）
  - 每天都会触发（无交易日概念）

**时区处理**：
- **A股**：使用中国时区（UTC+8），交易时间 9:30-15:00
- **美股**：使用美国东部时区（UTC-5/UTC-4，考虑夏令时），交易时间 9:30-16:00（ET）
- **港股**：使用香港时区（UTC+8），交易时间 9:30-16:00（HKT）
- **加密货币**：使用 UTC 时区，逻辑时间点基于 UTC 00:00

**时区实现方案**：
```python
import pytz
from datetime import datetime

MARKET_TIMEZONES = {
    'A_STOCK': pytz.timezone('Asia/Shanghai'),
    'US_STOCK': pytz.timezone('America/New_York'),
    'HK_STOCK': pytz.timezone('Asia/Hong_Kong'),
    'CRYPTO': pytz.UTC,
}

MARKET_TRADING_HOURS = {
    'A_STOCK': {
        'open': (9, 30),      # 9:30
        'close': (15, 0),     # 15:00
        'before_open': (9, 25),  # 9:25
        'after_close': (15, 5),  # 15:05
    },
    'US_STOCK': {
        'open': (9, 30),      # 9:30 ET
        'close': (16, 0),     # 16:00 ET
        'before_open': (9, 25),  # 9:25 ET
        'after_close': (16, 5),  # 16:05 ET
    },
    'HK_STOCK': {
        'open': (9, 30),      # 9:30 HKT
        'close': (16, 0),     # 16:00 HKT
        'before_open': (9, 25),  # 9:25 HKT
        'after_close': (16, 5),  # 16:05 HKT
    },
    'CRYPTO': {
        'open': (0, 0),       # 00:00 UTC (逻辑时间)
        'close': (23, 59),    # 23:59 UTC (逻辑时间)
        'before_open': (0, 0),   # 00:00 UTC
        'after_close': (23, 59),  # 23:59 UTC
    },
}

def get_market_time(current_utc_time: datetime, market_type: str, time_point: str) -> datetime:
    """获取市场时间"""
    tz = MARKET_TIMEZONES[market_type]
    market_local_time = current_utc_time.astimezone(tz)
    
    if market_type == 'CRYPTO':
        # 加密货币：使用逻辑时间点
        hour, minute = MARKET_TRADING_HOURS[market_type][time_point]
        return market_local_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        # 股票市场：使用实际交易时间
        hour, minute = MARKET_TRADING_HOURS[market_type][time_point]
        return market_local_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
```

**限制**：
- 时间精度受限于 `ExecRequest` 的触发时间
- 无法实现精确到秒的定时触发（但可以近似）
- 加密货币市场的"开盘收盘"概念是逻辑性的，不是实际的交易时间

### Decision 3: 交易日处理（get_trade_days）

**选择**：根据市场类型提供不同的交易日处理逻辑。

**理由**：
- 股票市场有交易日概念（需要跳过节假日）
- 加密货币市场是 7x24 交易（每天都是交易日）
- 需要兼容 JoinQuant 的 `get_trade_days()` API

**实现方式**：
```python
def get_trade_days(start_date, end_date, market_type=None):
    """获取交易日列表"""
    if is_crypto_market(market_type or detect_market_type()):
        # 加密货币：返回所有日期（7x24 交易）
        return generate_all_dates(start_date, end_date)
    else:
        # 股票市场：返回实际交易日（排除节假日）
        return get_stock_trade_days(start_date, end_date, market_type)
```

**市场类型适配**：
- **股票市场**：返回实际交易日列表，排除周末和节假日
- **加密货币市场**：返回所有日期（每天都是交易日）

**交易日历数据来源**：
- **数据来源**：使用静态配置文件 + 动态更新机制
  - 初始数据：内置常见市场的交易日历（A股、美股、港股）
  - 更新机制：支持通过配置文件或 API 更新节假日数据
  - 数据格式：JSON 或 CSV 格式，包含市场类型、日期、是否交易日等信息

**交易日历实现方案**：
```python
# engine/compat/trade_calendar.py
import json
from datetime import datetime, timedelta
from pathlib import Path

class TradeCalendar:
    """交易日历管理器"""
    
    def __init__(self, calendar_file: Optional[str] = None):
        self.calendar_file = calendar_file or 'trade_calendar.json'
        self.calendar_data = self._load_calendar()
    
    def _load_calendar(self) -> dict:
        """加载交易日历数据"""
        try:
            with open(self.calendar_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # 使用内置默认日历
            return self._get_default_calendar()
    
    def _get_default_calendar(self) -> dict:
        """获取默认交易日历（示例）"""
        return {
            'A_STOCK': {
                'holidays': [
                    '2024-01-01',  # 元旦
                    '2024-02-10',  # 春节
                    # ... 更多节假日
                ],
                'weekends': [5, 6],  # 周六、周日
            },
            'US_STOCK': {
                'holidays': [
                    '2024-01-01',  # New Year's Day
                    '2024-07-04',  # Independence Day
                    # ... 更多节假日
                ],
                'weekends': [5, 6],  # Saturday, Sunday
            },
            'HK_STOCK': {
                'holidays': [
                    '2024-01-01',  # New Year's Day
                    '2024-02-10',  # Chinese New Year
                    # ... 更多节假日
                ],
                'weekends': [5, 6],  # Saturday, Sunday
            },
        }
    
    def is_trade_day(self, date: datetime, market_type: str) -> bool:
        """判断是否为交易日"""
        if market_type == 'CRYPTO':
            return True  # 加密货币每天都是交易日
        
        market_cal = self.calendar_data.get(market_type, {})
        
        # 检查是否为周末
        if date.weekday() in market_cal.get('weekends', [5, 6]):
            return False
        
        # 检查是否为节假日
        date_str = date.strftime('%Y-%m-%d')
        if date_str in market_cal.get('holidays', []):
            return False
        
        return True
    
    def get_trade_days(self, start_date: datetime, end_date: datetime, market_type: str) -> List[str]:
        """获取交易日列表"""
        if market_type == 'CRYPTO':
            # 加密货币：返回所有日期
            days = []
            current = start_date
            while current <= end_date:
                days.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            return days
        
        # 股票市场：返回实际交易日
        days = []
        current = start_date
        while current <= end_date:
            if self.is_trade_day(current, market_type):
                days.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        return days
```

**交易日历更新机制**：
- **配置文件更新**：支持通过 `trade_calendar.json` 配置文件更新节假日
- **API 更新**：未来可支持通过 API 从外部服务获取最新交易日历
- **自动更新**：可配置定期检查并更新交易日历（如每月更新一次）

### Decision 4: 全局变量（g）

**选择**：使用模块级别的全局对象，每个策略文件有独立的 `g` 对象。

**理由**：
- 简单直接，符合 JoinQuant 的使用习惯
- 不需要修改 Context 结构
- 线程安全（每个策略执行在独立线程中）

**实现方式**：
```python
# 在策略加载时注入 g 对象
g = type('g', (), {})()  # 创建空对象
strategy_module.g = g   # 注入到策略模块

# 策略代码中使用
g.security = 'BTCUSDT'
```

### Decision 5: 日志模块（log）

**选择**：提供简单的日志模块，支持标准日志级别，输出到标准输出。

**理由**：
- 满足基本日志需求
- 实现简单，不需要复杂的日志系统
- 可以后续扩展为更强大的日志系统

**实现方式**：
```python
class Log:
    def info(self, msg): print(f"[INFO] {msg}")
    def warn(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def debug(self, msg): print(f"[DEBUG] {msg}")
    def set_level(self, category, level): pass  # 简化实现

log = Log()
```

### Decision 6: 下单函数（order_value, order_target）

**选择**：在模块级别提供全局函数，内部调用 `context` 的下单方法。根据市场类型调整数量单位。

**理由**：
- 保持 API 兼容性
- 不需要修改 Context 类
- 实现简单
- 股票市场按"股"计算，加密货币按"数量"计算

**实现方式**：
```python
def order_value(symbol, value, price=None):
    context = get_context()
    if price is None:
        price = float(context.current_bar.close)
    quantity = value / price
    
    # 股票市场：数量为整数（股）
    if is_stock_market(symbol):
        quantity = int(quantity)
    
    return context.order_buy(symbol, quantity, price)

def order_target(symbol, target_qty, price=None):
    context = get_context()
    current_qty = get_position_qty(context, symbol)
    diff = target_qty - current_qty
    
    # 股票市场：数量为整数（股）
    if is_stock_market(symbol):
        diff = int(diff)
    
    if diff > 0:
        return context.order_buy(symbol, diff, price)
    elif diff < 0:
        return context.order_sell(symbol, abs(diff), price)
```

**选择**：在模块级别提供全局函数，内部调用 `context` 的下单方法。

**理由**：
- 保持 API 兼容性
- 不需要修改 Context 类
- 实现简单

**实现方式**：
```python
def order_value(symbol, value, price=None):
    context = get_context()
    if price is None:
        price = float(context.current_bar.close)
    quantity = value / price
    return context.order_buy(symbol, quantity, price)

def order_target(symbol, target_qty, price=None):
    context = get_context()
    current_qty = get_position_qty(context, symbol)
    diff = target_qty - current_qty
    if diff > 0:
        return context.order_buy(symbol, diff, price)
    elif diff < 0:
        return context.order_sell(symbol, abs(diff), price)
```

### Decision 7: Context 属性扩展

**选择**：扩展 `Portfolio` 和 `Context` 类，添加兼容属性，同时保持向后兼容。

**理由**：
- 最小化代码修改
- 保持现有功能不变
- 提供兼容接口

**实现方式**：
```python
class Portfolio:
    def __init__(self):
        self.positions_list = []  # 原有列表
        self.positions_dict = {}  # 新增字典
    
    @property
    def positions(self):
        # 返回字典式访问接口
        return self.positions_dict
    
    @property
    def available_cash(self):
        # 从 account 计算
        return self._calculate_available_cash()
    
    @property
    def positions_value(self):
        # 计算持仓市值
        return self._calculate_positions_value()
```

### Decision 8: 成交记录查询（get_trades）

**选择**：从 `context._completed_orders` 中提取成交记录，转换为 JoinQuant 格式。

**理由**：
- 利用现有数据
- 不需要额外的数据存储
- 格式转换简单

**实现方式**：
```python
def get_trades():
    context = get_context()
    trades = {}
    for order in context._completed_orders:
        if order.status == "FILLED":
            trades[order.order_id] = {
                'security': order.symbol,
                'price': order.avg_fill_price,
                'amount': order.filled_qty,
                # ... 其他字段
            }
    return trades
```

## Risks / Trade-offs

### Risk 1: 市场类型识别错误

**风险**：如果标的代码格式不规范，可能导致市场类型识别错误，影响策略行为。

**缓解**：
- 提供明确的市场类型识别规则文档
- 支持显式指定市场类型（通过参数或配置）
- 在日志中记录市场类型识别结果，便于调试

### Risk 2: 定时运行精度不足

**风险**：`run_daily()` 的时间精度受限于 `ExecRequest` 的触发时间，可能无法精确匹配 JoinQuant 的行为。加密货币市场的"开盘收盘"概念是逻辑性的，可能与用户期望不一致。

**缓解**：
- 在文档中说明时间精度的限制
- 提供近似的时间匹配逻辑（如 "开盘前" 可以匹配到第一个 `before_trading` 调用）
- 明确说明加密货币市场的"开盘收盘"是逻辑性概念，不是实际交易时间

### Risk 3: 全局变量线程安全

**风险**：如果多个策略实例共享同一个策略文件，`g` 对象可能被并发访问。

**缓解**：
- 每个策略执行在独立线程中
- 每个策略文件加载时创建独立的 `g` 对象
- 策略管理系统保证同一策略的串行执行

### Risk 4: API 行为差异

**风险**：某些 API 的行为可能与 JoinQuant 不完全一致，特别是加密货币市场的特殊处理可能导致与股票市场的行为差异。

**缓解**：
- 在文档中明确说明行为差异
- 区分股票市场和加密货币市场的行为差异
- 提供迁移指南和示例
- 收集用户反馈，持续改进

**风险**：某些 API 的行为可能与 JoinQuant 不完全一致，导致策略行为差异。

**缓解**：
- 在文档中明确说明行为差异
- 提供迁移指南和示例
- 收集用户反馈，持续改进

### Risk 5: 性能影响

**风险**：兼容层可能带来性能开销（如字典式持仓访问需要维护两套数据结构）。

**缓解**：
- 性能影响较小，可以接受
- 如果性能成为瓶颈，可以后续优化

## Migration Plan

### Phase 1: 基础兼容功能（高优先级）

1. 实现 `g` 全局变量
2. 实现 `log` 模块
3. 扩展 Context 属性（`current_dt`, `available_cash`, `positions_value`）
4. 实现 `order_value()` 和 `order_target()`

### Phase 2: 定时运行机制（中优先级）

1. 实现 `run_daily()` 函数注册
2. 在引擎中集成定时函数调用逻辑
3. 实现时间匹配逻辑

### Phase 3: 成交记录和参数兼容（低优先级）

1. 实现 `get_trades()`
2. 实现 `get_bars()` 的 `unit` 参数兼容
3. 实现 `set_benchmark()`, `set_option()`, `set_order_cost()`（简化版本）

### Phase 4: 测试和文档

1. 使用 `double_mean.py` 作为测试用例
2. 更新迁移指南
3. 创建兼容性测试套件

## Open Questions

1. **定时运行精度**：是否需要支持更精确的时间触发？如果需要，可能需要扩展 `ExecRequest` 协议。
2. **日志集成**：是否需要将日志集成到系统的日志系统？还是保持简单的标准输出？
3. **持仓字典更新**：持仓字典如何与列表保持同步？是否需要实时更新？
4. **API 版本管理**：是否需要提供 API 版本管理，以便后续可以废弃某些兼容 API？
5. **市场类型配置**：是否需要支持配置文件或参数显式指定市场类型，而不完全依赖标的代码格式？
6. **时区处理**：美股和港股涉及不同时区，如何正确处理时区和交易时间？
7. **交易日历**：股票市场的交易日历数据来源？是否需要支持自定义交易日历？

