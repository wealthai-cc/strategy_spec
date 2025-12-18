# Python SDK 实现规范

## 1. 概述

### 1.1 背景及目标

WealthAI Python SDK 为量化策略提供本地化的查询接口，支持交易规则查询、佣金费率查询和数据转换等核心功能。SDK 采用本地文件读取方式，避免网络请求，提供毫秒级甚至微秒级的响应速度。

**核心目标**：
- **本地优先**：所有数据查询通过本地配置文件，零网络延迟
- **高性能**：首次查询毫秒级，缓存命中微秒级
- **线程安全**：支持多线程并发查询，无竞态条件
- **类型安全**：完整的类型注解支持，符合现代Python标准
- **灵活配置**：支持多种配置路径策略，适应不同部署环境

### 1.2 版本信息

- **当前版本**：1.0.0
- **Python 要求**：>= 3.10
- **依赖项**：pandas >= 1.0.0

### 1.3 设计原则

1. **无状态设计**：SDK 本身不维护业务状态，仅提供数据查询服务
2. **缓存优先**：使用内存缓存优化性能，减少文件 I/O
3. **错误明确**：提供清晰的异常类型和错误信息
4. **向后兼容**：保证接口稳定性，遵循语义化版本控制

## 2. 模块架构

### 2.1 模块划分

```
wealthai_sdk/
├── __init__.py          # 模块入口，公共接口导出
├── trading.py           # 交易规则和佣金费率查询
├── config.py            # 配置管理（路径查找、环境适配）
├── data_utils.py        # 数据转换工具（DataFrame 支持）
└── exceptions.py        # 异常类定义
```

### 2.2 模块职责

#### 2.2.1 trading.py - 交易数据查询模块

**职责**：
- 提供交易规则查询接口 `get_trading_rule()`
- 提供佣金费率查询接口 `get_commission_rates()`
- 实现线程安全的缓存机制
- 管理配置文件的加载和解析

**核心类**：
- `TradingDataCache`：线程安全的数据缓存实现

**核心函数**：
- `get_trading_rule(broker, symbol)`：查询交易规则
- `get_commission_rates(broker, symbol)`：查询佣金费率
- `clear_cache()`：清空所有缓存

#### 2.2.2 config.py - 配置管理模块

**职责**：
- 确定配置文件目录（支持多优先级策略）
- 提供配置文件路径查询接口
- 自动创建必要的配置目录

**核心类**：
- `Config`：配置管理器，单例模式

**配置优先级**（从高到低）：
1. 环境变量 `WEALTHAI_CONFIG_DIR`
2. 项目根目录 `<project_root>/config`
3. 用户主目录 `~/.wealthai`

#### 2.2.3 data_utils.py - 数据转换模块

**职责**：
- 将 Bar 对象列表转换为 pandas DataFrame
- 支持字典和对象两种 Bar 格式
- 提供类型安全的数据转换

**核心函数**：
- `bars_to_dataframe(bars)`：Bar 列表转 DataFrame

#### 2.2.4 exceptions.py - 异常定义模块

**职责**：
- 定义 SDK 专用异常类型
- 提供清晰的错误信息和上下文

**异常层次**：
```
WealthAISDKError (基类)
├── NotFoundError (资源未找到)
└── ParseError (解析错误)
```

## 3. 接口定义

### 3.1 交易规则查询

#### 3.1.1 get_trading_rule

```python
def get_trading_rule(broker: str, symbol: str) -> Dict[str, Any]
```

**功能描述**：
查询指定交易所和交易对的交易规则，包括最小下单量、价格精度、杠杆限制等参数。

**参数**：
- `broker: str` - 交易所/券商标识（如：`binance`、`okx`、`huobi`）
- `symbol: str` - 交易品种标识（如：`BTCUSDT`、`ETHUSDT`）

**返回值**：`Dict[str, Any]`
```python
{
    'symbol': str,              # 品种代号
    'min_quantity': float,      # 最小下单量
    'quantity_step': float,     # 数量步进（必须为此值的整数倍）
    'min_price': float,         # 最小价格
    'price_tick': float,        # 价格最小变动单位
    'price_precision': int,     # 价格精度（小数位数）
    'quantity_precision': int,  # 数量精度（小数位数）
    'max_leverage': float       # 最大杠杆倍数（默认 1.0）
}
```

**异常**：
- `NotFoundError` - 配置文件不存在或品种未配置
- `ParseError` - 配置文件格式错误或字段缺失

**性能指标**：
- 首次查询：< 5ms（包含文件读取和解析）
- 缓存命中：< 100μs

**使用示例**：
```python
from wealthai_sdk import get_trading_rule, NotFoundError, ParseError

try:
    rule = get_trading_rule("binance", "BTCUSDT")
    
    # 获取规则参数
    min_qty = rule['min_quantity']          # 0.00001
    qty_step = rule['quantity_step']        # 0.00001
    price_precision = rule['price_precision'] # 2
    max_leverage = rule['max_leverage']      # 125.0
    
    # 校验订单数量
    order_qty = 0.5
    if order_qty >= min_qty:
        # 调整为步进的整数倍
        adjusted_qty = round(order_qty / qty_step) * qty_step
        print(f"调整后数量: {adjusted_qty}")
        
except NotFoundError as e:
    print(f"交易规则未找到: {e}")
except ParseError as e:
    print(f"配置解析失败: {e}")
```

### 3.2 佣金费率查询

#### 3.2.1 get_commission_rates

```python
def get_commission_rates(broker: str, symbol: str) -> Dict[str, float]
```

**功能描述**：
查询指定交易所和交易对的 Maker/Taker 佣金费率，用于交易成本计算和策略收益评估。

**参数**：
- `broker: str` - 交易所/券商标识
- `symbol: str` - 交易品种标识

**返回值**：`Dict[str, float]`
```python
{
    'maker_fee_rate': float,  # Maker 手续费率（如 0.0002 = 0.02%）
    'taker_fee_rate': float   # Taker 手续费率（如 0.0004 = 0.04%）
}
```

**异常**：
- `NotFoundError` - 配置文件不存在或费率未配置
- `ParseError` - 配置文件格式错误或字段缺失

**性能指标**：
- 首次查询：< 5ms
- 缓存命中：< 100μs

**使用示例**：
```python
from wealthai_sdk import get_commission_rates

try:
    rates = get_commission_rates("binance", "BTCUSDT")
    
    # 计算交易成本
    order_value = 10000.0  # 订单金额（USDT）
    
    # Maker 订单（限价单被动成交）
    maker_commission = order_value * rates['maker_fee_rate']
    print(f"Maker 手续费: {maker_commission} USDT")
    
    # Taker 订单（市价单主动成交）
    taker_commission = order_value * rates['taker_fee_rate']
    print(f"Taker 手续费: {taker_commission} USDT")
    
except Exception as e:
    print(f"费率查询失败: {e}")
```

### 3.3 缓存管理

#### 3.3.1 clear_cache

```python
def clear_cache() -> None
```

**功能描述**：
清空所有缓存数据，强制下次查询重新读取配置文件。

**使用场景**：
- 配置文件更新后需要立即生效
- 测试环境中需要验证最新配置
- 内存优化（长期运行的策略）

**使用示例**：
```python
from wealthai_sdk import clear_cache, get_trading_rule

# 更新配置文件后清空缓存
clear_cache()

# 下次查询将读取最新配置
rule = get_trading_rule("binance", "BTCUSDT")
```

### 3.4 数据转换

#### 3.4.1 bars_to_dataframe

```python
def bars_to_dataframe(bars: List[Any]) -> pd.DataFrame
```

**功能描述**：
将 Bar 对象列表转换为 pandas DataFrame，便于使用 pandas 进行技术分析计算。

**参数**：
- `bars: List[Any]` - Bar 对象列表，支持字典和对象两种格式

**Bar 对象结构**：
```python
{
    'open': float,        # 开盘价
    'high': float,        # 最高价
    'low': float,         # 最低价
    'close': float,       # 收盘价
    'volume': float,      # 成交量
    'close_time': int     # 收盘时间戳（Unix毫秒）
}
```

**返回值**：`pd.DataFrame`
- 列：`['open', 'high', 'low', 'close', 'volume']`
- 索引：`close_time`（时间戳）
- 数据类型：所有列为 `float64`

**使用示例**：
```python
from wealthai_sdk import bars_to_dataframe
import pandas as pd

# 假设从 context.history() 获取 Bar 列表
bars = context.history('BTCUSDT', 20, '1h')

# 转换为 DataFrame
df = bars_to_dataframe(bars)

# 使用 pandas 进行技术分析
ma_20 = df['close'].mean()              # 20 周期均价
std_20 = df['close'].std()              # 标准差
returns = df['close'].pct_change()      # 收益率

# 计算布林带
upper_band = ma_20 + 2 * std_20
lower_band = ma_20 - 2 * std_20

print(f"MA(20): {ma_20:.2f}")
print(f"Upper Band: {upper_band:.2f}")
print(f"Lower Band: {lower_band:.2f}")
```

## 4. 异常处理机制

### 4.1 异常类型层次

```python
WealthAISDKError                    # SDK 基础异常
├── NotFoundError                   # 资源未找到异常
│   ├── broker: str                # 交易所标识
│   ├── symbol: str                # 交易品种
│   └── resource_type: str         # 资源类型描述
└── ParseError                      # 解析错误异常
    ├── file_path: str             # 配置文件路径
    └── reason: str                # 错误原因
```

### 4.2 异常详细说明

#### 4.2.1 NotFoundError

**触发条件**：
1. 配置文件不存在（如 `config/trading_rules/binance.json` 缺失）
2. 配置文件存在但不包含指定 symbol 的配置

**异常信息格式**：
```
未找到 {broker}/{symbol} 的{resource_type}
```

**处理建议**：
```python
try:
    rule = get_trading_rule("binance", "NEWCOIN")
except NotFoundError as e:
    # 选项1：使用默认值
    default_rule = {
        'min_quantity': 0.01,
        'quantity_step': 0.01,
        'price_precision': 2,
        'quantity_precision': 2,
        'max_leverage': 1.0
    }
    
    # 选项2：记录日志并跳过
    logger.warning(f"交易规则未找到: {e.broker}/{e.symbol}")
    
    # 选项3：通知管理员添加配置
    notify_admin(f"需要添加 {e.broker}/{e.symbol} 的配置")
```

#### 4.2.2 ParseError

**触发条件**：
1. JSON 格式错误（语法错误）
2. 必需字段缺失
3. 字段类型错误（无法转换为预期类型）

**异常信息格式**：
```
解析文件 {file_path} 失败: {reason}
```

**处理建议**：
```python
try:
    rule = get_trading_rule("binance", "BTCUSDT")
except ParseError as e:
    # 记录详细错误信息
    logger.error(f"配置解析失败")
    logger.error(f"文件: {e.file_path}")
    logger.error(f"原因: {e.reason}")
    
    # 通知管理员修复配置文件
    alert_admin({
        'type': 'config_parse_error',
        'file': e.file_path,
        'reason': e.reason
    })
    
    # 使用降级策略（如禁用该交易对）
    disable_trading_pair("binance", "BTCUSDT")
```

### 4.3 错误处理最佳实践

#### 4.3.1 策略初始化阶段

```python
def initialize(context):
    """策略初始化"""
    try:
        # 预加载所有需要的交易规则
        g.btc_rule = get_trading_rule("binance", "BTCUSDT")
        g.eth_rule = get_trading_rule("binance", "ETHUSDT")
        g.commission = get_commission_rates("binance", "BTCUSDT")
        
    except NotFoundError as e:
        # 初始化阶段的错误应该中断策略启动
        log.error(f"必需的配置缺失: {e}")
        raise RuntimeError("策略初始化失败，缺少必需配置")
        
    except ParseError as e:
        # 配置错误也应该中断启动
        log.error(f"配置文件损坏: {e}")
        raise RuntimeError("策略初始化失败，配置文件错误")
```

#### 4.3.2 策略执行阶段

```python
def handle_bar(context, bar):
    """策略执行"""
    try:
        # 动态查询新品种的规则（可选）
        rule = get_trading_rule("binance", context.symbol)
        
    except NotFoundError:
        # 执行阶段的错误可以容错处理
        log.warning(f"品种 {context.symbol} 规则未找到，跳过交易")
        return
        
    except ParseError as e:
        # 记录错误但继续运行
        log.error(f"规则解析失败: {e.reason}")
        return
    
    # 正常执行交易逻辑
    if should_buy(context, bar):
        quantity = calculate_quantity(rule)
        order_value(quantity)
```

## 5. 配置文件规范

### 5.1 配置目录结构

```
config/
├── trading_rules/              # 交易规则配置
│   ├── binance.json           # 币安交易规则
│   ├── okx.json               # OKX 交易规则
│   ├── huobi.json             # 火币交易规则
│   └── bybit.json             # Bybit 交易规则
└── commission_rates/           # 佣金费率配置
    ├── binance.json           # 币安佣金费率
    ├── okx.json               # OKX 佣金费率
    ├── huobi.json             # 火币佣金费率
    └── bybit.json             # Bybit 佣金费率
```

### 5.2 交易规则配置格式

**文件路径**：`config/trading_rules/{broker}.json`

**JSON 结构**：
```json
{
    "BTCUSDT": {
        "symbol": "BTCUSDT",
        "min_quantity": 0.00001,
        "quantity_step": 0.00001,
        "min_price": 0.01,
        "price_tick": 0.01,
        "price_precision": 2,
        "quantity_precision": 5,
        "max_leverage": 125.0
    },
    "ETHUSDT": {
        "symbol": "ETHUSDT",
        "min_quantity": 0.0001,
        "quantity_step": 0.0001,
        "min_price": 0.01,
        "price_tick": 0.01,
        "price_precision": 2,
        "quantity_precision": 4,
        "max_leverage": 75.0
    }
}
```

**字段说明**：
- `symbol` (string, 必需)：品种代号，应与 key 一致
- `min_quantity` (number, 必需)：最小下单量
- `quantity_step` (number, 必需)：数量步进
- `min_price` (number, 必需)：最小价格
- `price_tick` (number, 必需)：价格最小变动单位
- `price_precision` (integer, 必需)：价格精度（小数位数）
- `quantity_precision` (integer, 必需)：数量精度（小数位数）
- `max_leverage` (number, 可选)：最大杠杆倍数，默认 1.0

### 5.3 佣金费率配置格式

**文件路径**：`config/commission_rates/{broker}.json`

**JSON 结构**：
```json
{
    "BTCUSDT": {
        "maker_fee_rate": 0.0002,
        "taker_fee_rate": 0.0004
    },
    "ETHUSDT": {
        "maker_fee_rate": 0.0002,
        "taker_fee_rate": 0.0004
    }
}
```

**字段说明**：
- `maker_fee_rate` (number, 必需)：Maker 手续费率（小数形式）
- `taker_fee_rate` (number, 必需)：Taker 手续费率（小数形式）

**费率表示**：
- 0.0002 = 0.02%
- 0.0004 = 0.04%
- 0.001 = 0.1%

### 5.4 配置文件管理

#### 5.4.1 配置更新流程

1. **停止策略**（可选，取决于是否需要立即生效）
2. **更新配置文件**
3. **调用 `clear_cache()`** 清空缓存
4. **重启策略**或等待下次查询自动加载

#### 5.4.2 配置验证

建议在更新配置后进行验证：

```python
import json
from pathlib import Path

def validate_trading_rules(broker: str):
    """验证交易规则配置文件"""
    file_path = Path(f"config/trading_rules/{broker}.json")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        required_fields = [
            'symbol', 'min_quantity', 'quantity_step',
            'min_price', 'price_tick', 'price_precision',
            'quantity_precision'
        ]
        
        for symbol, rule in data.items():
            # 检查必需字段
            for field in required_fields:
                if field not in rule:
                    print(f"错误: {symbol} 缺少字段 {field}")
                    return False
            
            # 检查数据类型
            if not isinstance(rule['price_precision'], int):
                print(f"错误: {symbol} 的 price_precision 应为整数")
                return False
                
        print(f"✓ {broker} 交易规则配置验证通过")
        return True
        
    except json.JSONDecodeError as e:
        print(f"错误: JSON 格式错误 - {e}")
        return False
    except FileNotFoundError:
        print(f"错误: 配置文件不存在 - {file_path}")
        return False

# 验证所有配置
validate_trading_rules("binance")
validate_trading_rules("okx")
```

## 6. 缓存机制

### 6.1 缓存策略

#### 6.1.1 缓存键设计

```python
# 交易规则缓存键
cache_key = f"trading_rule:{broker}:{symbol}"
# 示例: "trading_rule:binance:BTCUSDT"

# 佣金费率缓存键
cache_key = f"commission_rates:{broker}:{symbol}"
# 示例: "commission_rates:binance:BTCUSDT"
```

#### 6.1.2 缓存生命周期

- **创建时机**：首次查询成功后
- **失效时机**：调用 `clear_cache()` 或进程重启
- **更新策略**：不自动更新，需手动清空缓存

### 6.2 线程安全实现

使用 `threading.RLock` 实现可重入锁：

```python
class TradingDataCache:
    """线程安全的交易数据缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()  # 可重入锁
    
    def get(self, key: str) -> Any:
        """线程安全的获取操作"""
        with self._lock:
            return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """线程安全的设置操作"""
        with self._lock:
            self._cache[key] = value
    
    def clear_cache(self) -> None:
        """线程安全的清空操作"""
        with self._lock:
            self._cache.clear()
```

**线程安全保证**：
- 所有缓存操作都在锁保护下进行
- 支持多线程并发读写
- 避免数据竞争和脏读

### 6.3 缓存性能分析

| 场景 | 首次查询 | 缓存命中 | 并发查询（10线程） |
|------|---------|---------|------------------|
| 交易规则 | ~3ms | ~50μs | ~100μs |
| 佣金费率 | ~2ms | ~50μs | ~100μs |

**性能优化建议**：
1. 策略初始化时预加载常用配置
2. 避免在循环中频繁查询同一配置
3. 长期运行的策略定期清理缓存（释放内存）

## 7. 类型安全与现代 Python 特性

### 7.1 类型注解

所有公共接口提供完整的类型注解：

```python
from typing import Dict, Any, List
import pandas as pd

def get_trading_rule(broker: str, symbol: str) -> Dict[str, Any]:
    """带类型注解的接口"""
    ...

def get_commission_rates(broker: str, symbol: str) -> Dict[str, float]:
    """明确返回值类型"""
    ...

def bars_to_dataframe(bars: List[Any]) -> pd.DataFrame:
    """支持 pandas 类型"""
    ...
```

### 7.2 Python 3.10+ 特性

使用联合类型语法（PEP 604）：

```python
# 旧语法 (Python 3.9-)
from typing import Optional
def detect_market_type(symbol: Optional[str]) -> MarketType:
    ...

# 新语法 (Python 3.10+)
def detect_market_type(symbol: str | None) -> MarketType:
    ...
```

### 7.3 类型检查支持

支持主流类型检查器：
- **mypy**：静态类型检查
- **pyright/basedpyright**：微软开发的类型检查器
- **pyre**：Facebook 的类型检查器

## 8. 测试与质量保证

### 8.1 单元测试覆盖

```python
# tests/wealthaisdk/test_trading.py
import unittest
from wealthai_sdk import (
    get_trading_rule,
    get_commission_rates,
    NotFoundError,
    ParseError,
    clear_cache
)

class TestTradingFunctions(unittest.TestCase):
    """交易功能测试"""
    
    def setUp(self):
        """测试前准备"""
        clear_cache()
    
    def test_get_trading_rule_success(self):
        """测试成功获取交易规则"""
        rule = get_trading_rule("binance", "BTCUSDT")
        
        self.assertIn('symbol', rule)
        self.assertIn('min_quantity', rule)
        self.assertEqual(rule['symbol'], 'BTCUSDT')
    
    def test_get_trading_rule_not_found(self):
        """测试品种不存在的情况"""
        with self.assertRaises(NotFoundError):
            get_trading_rule("binance", "UNKNOWN")
    
    def test_cache_mechanism(self):
        """测试缓存机制"""
        # 首次查询
        rule1 = get_trading_rule("binance", "BTCUSDT")
        
        # 缓存命中
        rule2 = get_trading_rule("binance", "BTCUSDT")
        
        # 应该返回相同的对象
        self.assertEqual(rule1, rule2)
```

### 8.2 测试覆盖率目标

- **行覆盖率**：> 90%
- **分支覆盖率**：> 85%
- **函数覆盖率**：100%

### 8.3 性能测试

```python
import time
from wealthai_sdk import get_trading_rule, clear_cache

def benchmark_query_performance():
    """性能基准测试"""
    # 首次查询（包含文件读取）
    clear_cache()
    start = time.perf_counter()
    rule = get_trading_rule("binance", "BTCUSDT")
    first_query_time = (time.perf_counter() - start) * 1000
    
    # 缓存命中查询
    start = time.perf_counter()
    rule = get_trading_rule("binance", "BTCUSDT")
    cached_query_time = (time.perf_counter() - start) * 1000
    
    print(f"首次查询: {first_query_time:.2f} ms")
    print(f"缓存命中: {cached_query_time:.2f} ms")
    
    assert first_query_time < 10.0, "首次查询应 < 10ms"
    assert cached_query_time < 1.0, "缓存命中应 < 1ms"
```

## 9. 版本兼容性

### 9.1 语义化版本控制

遵循 [SemVer 2.0.0](https://semver.org/lang/zh-CN/) 规范：

- **主版本号（MAJOR）**：不兼容的 API 变更
- **次版本号（MINOR）**：向后兼容的功能新增
- **修订号（PATCH）**：向后兼容的问题修正

### 9.2 兼容性承诺

#### 9.2.1 保证向后兼容

✅ **允许的变更**（不增加主版本号）：
- 添加新的可选参数（有默认值）
- 添加新的返回字段
- 添加新的公共函数
- 性能优化
- Bug 修复

❌ **破坏性变更**（需增加主版本号）：
- 删除公共 API
- 修改函数签名（参数顺序、类型）
- 删除返回值中的字段
- 修改异常类型

#### 9.2.2 版本升级指南

**从 0.x 升级到 1.0**：
```python
# 0.x 版本
from wealthai_sdk import get_trading_rule

# 1.0 版本 - 完全兼容
from wealthai_sdk import get_trading_rule  # 无需修改
```

**从 1.x 升级到 2.0**（假设有破坏性变更）：
```python
# 1.x 版本
rule = get_trading_rule("binance", "BTCUSDT")
min_qty = rule['min_quantity']

# 2.x 版本 - 假设字段名变更
rule = get_trading_rule("binance", "BTCUSDT")
min_qty = rule['minimum_quantity']  # 字段名变更
```

### 9.3 弃用策略

采用两阶段弃用：

**阶段 1：标记为弃用**（次版本更新）
```python
import warnings

def old_function():
    warnings.warn(
        "old_function 已弃用，请使用 new_function 替代。"
        "该函数将在 2.0 版本中移除。",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

**阶段 2：移除**（主版本更新）
```python
# 在下一个主版本中完全移除 old_function
```

## 10. 最佳实践

### 10.1 策略开发最佳实践

#### 10.1.1 初始化阶段预加载

```python
def initialize(context):
    """策略初始化 - 预加载配置"""
    from wealthai_sdk import get_trading_rule, get_commission_rates
    
    # 预加载所有需要的规则
    g.rules = {}
    g.fees = {}
    
    for symbol in context.symbols:
        try:
            g.rules[symbol] = get_trading_rule(context.broker, symbol)
            g.fees[symbol] = get_commission_rates(context.broker, symbol)
        except Exception as e:
            log.error(f"加载 {symbol} 配置失败: {e}")
            raise
    
    log.info(f"成功加载 {len(g.rules)} 个品种的配置")
```

#### 10.1.2 订单参数校验

```python
def create_order(symbol, price, quantity):
    """创建订单前校验参数"""
    rule = g.rules[symbol]
    
    # 校验数量
    if quantity < rule['min_quantity']:
        quantity = rule['min_quantity']
        log.warning(f"数量调整为最小值: {quantity}")
    
    # 调整为步进的整数倍
    quantity = round(quantity / rule['quantity_step']) * rule['quantity_step']
    
    # 调整精度
    quantity = round(quantity, rule['quantity_precision'])
    price = round(price, rule['price_precision'])
    
    # 创建订单
    return order_target(symbol, quantity, price)
```

#### 10.1.3 成本计算

```python
def calculate_trading_cost(symbol, order_type, amount):
    """计算交易成本"""
    fees = g.fees[symbol]
    
    # 根据订单类型选择费率
    if order_type == "LIMIT":
        rate = fees['maker_fee_rate']
    else:
        rate = fees['taker_fee_rate']
    
    commission = amount * rate
    
    # 考虑滑点（可选）
    slippage_rate = 0.0001  # 0.01%
    slippage = amount * slippage_rate
    
    total_cost = commission + slippage
    return {
        'commission': commission,
        'slippage': slippage,
        'total': total_cost
    }
```

### 10.2 性能优化建议

#### 10.2.1 批量预加载

```python
# ❌ 不推荐：循环中重复查询
for symbol in symbols:
    rule = get_trading_rule("binance", symbol)  # 多次调用
    process(symbol, rule)

# ✅ 推荐：预加载到字典
rules = {s: get_trading_rule("binance", s) for s in symbols}
for symbol in symbols:
    process(symbol, rules[symbol])
```

#### 10.2.2 避免不必要的查询

```python
# ❌ 不推荐：每次都查询
def handle_bar(context, bar):
    rule = get_trading_rule("binance", context.symbol)
    # 使用 rule...

# ✅ 推荐：缓存在全局变量
def initialize(context):
    g.rule = get_trading_rule("binance", context.symbol)

def handle_bar(context, bar):
    # 使用 g.rule...
```

### 10.3 错误处理建议

#### 10.3.1 分层错误处理

```python
def initialize(context):
    """初始化阶段 - 严格错误处理"""
    try:
        rule = get_trading_rule("binance", "BTCUSDT")
    except (NotFoundError, ParseError) as e:
        log.error(f"致命错误: {e}")
        raise  # 中断策略启动

def handle_bar(context, bar):
    """执行阶段 - 容错处理"""
    try:
        rule = get_trading_rule("binance", context.symbol)
    except NotFoundError:
        log.warning(f"跳过未配置的品种: {context.symbol}")
        return  # 跳过本次执行
    except ParseError as e:
        log.error(f"配置错误: {e}")
        return  # 跳过本次执行
```

#### 10.3.2 降级策略

```python
def get_rule_with_fallback(broker, symbol):
    """带降级策略的规则查询"""
    try:
        return get_trading_rule(broker, symbol)
    except NotFoundError:
        # 使用保守的默认值
        log.warning(f"使用默认规则: {broker}/{symbol}")
        return {
            'min_quantity': 0.01,
            'quantity_step': 0.01,
            'price_precision': 2,
            'quantity_precision': 2,
            'max_leverage': 1.0
        }
```

## 11. 常见问题 (FAQ)

### Q1: 为什么使用本地文件而不是 API 查询？

**A**: 本地文件读取的优势：
1. **零网络延迟**：无需等待网络响应
2. **高可用性**：不受网络波动影响
3. **成本更低**：无 API 调用限制
4. **数据一致**：配置文件版本可控

交易规则和费率相对稳定，适合本地缓存。

### Q2: 配置文件更新后如何立即生效？

**A**: 两种方式：
```python
# 方式1：手动清空缓存
from wealthai_sdk import clear_cache
clear_cache()

# 方式2：重启策略进程
# 策略重启时会自动加载最新配置
```

### Q3: 如何处理多环境配置？

**A**: 使用环境变量指定配置目录：
```bash
# 开发环境
export WEALTHAI_CONFIG_DIR=/path/to/dev/config

# 生产环境
export WEALTHAI_CONFIG_DIR=/path/to/prod/config

# 测试环境
export WEALTHAI_CONFIG_DIR=/path/to/test/config
```

### Q4: SDK 是否支持异步查询？

**A**: 当前版本为同步实现。由于查询本身非常快（微秒级），异步收益有限。未来版本可能考虑添加异步支持。

### Q5: 如何监控 SDK 的性能？

**A**: 使用日志和性能计数器：
```python
import time
import logging

logger = logging.getLogger(__name__)

def measure_query_time():
    start = time.perf_counter()
    rule = get_trading_rule("binance", "BTCUSDT")
    elapsed = (time.perf_counter() - start) * 1000
    
    logger.info(f"查询耗时: {elapsed:.2f} ms")
    
    if elapsed > 10.0:
        logger.warning(f"查询较慢: {elapsed:.2f} ms")
```

### Q6: 配置文件可以放在数据库中吗？

**A**: 当前版本仅支持本地 JSON 文件。如需数据库支持，可以：
1. 实现自定义配置加载器
2. 定期将数据库内容同步到本地文件
3. 提交 Feature Request 建议添加数据库支持

### Q7: 如何扩展 SDK 添加自定义字段？

**A**: 配置文件支持额外字段：
```json
{
    "BTCUSDT": {
        "symbol": "BTCUSDT",
        "min_quantity": 0.00001,
        // ... 标准字段
        "custom_field": "custom_value"  // 自定义字段
    }
}
```

自定义字段会包含在返回结果中，但不会被 SDK 验证。

## 12. 相关文档

- [策略执行引擎规范](../strategy-engine/spec.md)
- [策略开发规范](../strategy-development/spec.md)
- [订单管理规范](../order/spec.md)
- [行情数据规范](../market-data/spec.md)
- [JoinQuant 迁移指南](../../../PRD/JoinQuant迁移指南.md)

## 13. 变更日志

### v1.0.0 (2024-12-16)

**初始版本**
- ✨ 实现交易规则查询接口
- ✨ 实现佣金费率查询接口
- ✨ 实现 DataFrame 转换工具
- ✨ 实现线程安全的缓存机制
- ✨ 实现多优先级配置路径支持
- 📝 完整的类型注解支持
- 🧪 完整的单元测试覆盖

---

**文档版本**: v1.0.0  
**最后更新**: 2024-12-16  
**维护者**: WealthAI Team
