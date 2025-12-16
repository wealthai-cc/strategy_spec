# Change: 添加 jqdata 模块兼容层（零代码修改）

## Why

JoinQuant 平台使用 `jqdatasdk` 作为数据访问接口，用户编写的策略代码大量使用 `jqdatasdk.get_price()`, `jqdatasdk.get_bars()` 等 API。为了吸引 JoinQuant 用户平滑迁移到我们的平台，需要提供 `jqdata`/`jqdatasdk` 兼容模块，让用户能够：

1. **直接复制 JoinQuant 策略代码**，无需修改业务逻辑
2. **保持原有语法**，支持 `jqdatasdk.get_price()` 等调用方式
3. **最小化修改**，只需替换 `import jqdatasdk` 为 `import jqdata`（我们的兼容模块），或完全不需要修改 import（如果模块名相同）

**核心目标**：实现零代码修改的平滑迁移体验。

## What Changes

- **ADDED**: `jqdata`/`jqdatasdk` 兼容模块（支持直接 import）
- **ADDED**: 模块级 API 函数（`get_price()`, `get_bars()` 等）
- **ADDED**: Context 对象的线程局部存储机制（Thread-local storage）
- **ADDED**: DataFrame 格式自动转换（Bar → pandas DataFrame）
- **ADDED**: JoinQuant 常用 API 映射（get_price, get_bars, get_fundamentals 等）
- **MODIFIED**: 策略执行引擎，在执行前设置 Context 到线程局部变量

**Non-Breaking**: 现有 API 保持不变，兼容层作为可选扩展

**关键特性**：
- 用户可以直接复制 JoinQuant 代码，只需修改一行 import（或完全不需要修改）
- 支持 `jqdatasdk.get_price()` 等模块级函数调用
- 自动将数据转换为 pandas DataFrame 格式
- 内部映射到我们的 `context.history()` 方法

## Impact

- **Affected specs**: 
  - `strategy-development` - 添加 jqdata 兼容模块说明
  - `strategy-engine` - 添加 Context 线程局部存储机制
- **Affected code**: 
  - 新增 `jqdata.py` 或 `jqdatasdk.py` 兼容模块
  - 引擎在执行策略前设置 Context 到线程局部变量
  - Context 对象扩展（添加 jqdata 风格方法，可选）
- **Affected docs**: 
  - 添加 JoinQuant 零代码迁移指南
  - 添加 jqdata API 映射文档
  - 添加迁移示例（展示直接复制代码的效果）

## Design Considerations

### JoinQuant jqdata 使用方式

JoinQuant 用户通常这样使用 jqdata：

```python
import jqdatasdk

def initialize(context):
    context.symbol = '000001.XSHE'

def handle_bar(context, bar):
    # 模块级函数调用
    df = jqdatasdk.get_price(context.symbol, count=20, frequency='1d')
    ma = df['close'].mean()
    
    if bar.close > ma:
        order_buy(context.symbol, 100)
```

**关键特点**：
- 使用 `jqdatasdk.get_price()` 等模块级函数
- 返回 pandas DataFrame 格式
- 不需要传递 context 参数
- 函数在模块级别调用

### 我们的框架使用方式

当前我们的框架使用方式：

```python
def initialize(context):
    context.symbol = 'BTCUSDT'

def handle_bar(context, bar):
    # Context 对象方法调用
    bars = context.history(context.symbol, 20, '1h')
    # 需要手动转换为 DataFrame 或使用 Bar 对象
```

**关键差异**：
- 需要通过 context 对象调用
- 返回 Bar 对象列表
- 需要手动处理数据格式

### 兼容方案：jqdata 模块兼容层

#### 核心设计

1. **创建兼容模块**：提供 `jqdata.py` 或 `jqdatasdk.py` 模块
2. **线程局部存储**：使用 thread-local storage 存储当前执行的 Context
3. **模块级函数**：提供 `get_price()`, `get_bars()` 等模块级函数
4. **自动映射**：内部映射到 `context.history()` 并转换为 DataFrame

#### 实现架构

```
策略代码
    ↓
import jqdatasdk  (我们的兼容模块)
    ↓
jqdatasdk.get_price() 调用
    ↓
从 thread-local 获取 Context
    ↓
调用 context.history()
    ↓
转换为 pandas DataFrame
    ↓
返回给策略
```

#### 使用示例

**JoinQuant 原始代码（完全不变）**：

```python
import jqdatasdk  # 替换为我们的兼容模块

def initialize(context):
    context.symbol = 'BTCUSDT'  # 只需修改交易品种格式

def handle_bar(context, bar):
    # 以下代码完全不变
    df = jqdatasdk.get_price(context.symbol, count=20, frequency='1h')
    ma = df['close'].mean()
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)  # 只需修改下单 API
```

**迁移步骤**：
1. 复制 JoinQuant 代码
2. 替换 `import jqdatasdk` 为 `import jqdata`（或保持原样，如果模块名相同）
3. 修改交易品种格式（如 '000001.XSHE' → 'BTCUSDT'）
4. 修改下单 API（`order_buy()` → `context.order_buy()`）

**代码修改量**：最小化，主要是格式转换，业务逻辑完全不变。

### 技术实现细节

#### 1. 线程局部存储（Thread-local Storage）

```python
import threading

# 线程局部变量存储当前 Context
_context_local = threading.local()

def set_context(context):
    """引擎在执行策略前调用，设置当前 Context"""
    _context_local.context = context

def get_context():
    """获取当前线程的 Context"""
    return getattr(_context_local, 'context', None)

def clear_context():
    """引擎在执行后调用，清理 Context"""
    if hasattr(_context_local, 'context'):
        delattr(_context_local, 'context')
```

#### 2. jqdata 兼容模块

```python
# jqdata.py 或 jqdatasdk.py
import pandas as pd
from .context_local import get_context

def get_price(symbol, count=None, end_date=None, frequency='1h', 
              fields=None, skip_paused=False, fq='pre'):
    """
    JoinQuant 风格的 get_price API
    
    参数兼容 JoinQuant API，但部分参数可能不支持（如 fq, skip_paused）
    """
    context = get_context()
    if context is None:
        raise RuntimeError("Context not available. This function must be called within strategy execution.")
    
    # 映射到我们的 history 方法
    bars = context.history(symbol, count or 20, frequency)
    
    # 转换为 DataFrame
    data = []
    for bar in bars:
        data.append({
            'time': bar.close_time,
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': float(bar.volume),
        })
    
    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    
    # 处理 fields 参数
    if fields:
        df = df[fields]
    
    return df

def get_bars(symbol, count=None, end_date=None, frequency='1h', 
             fields=None, skip_paused=False, fq='pre'):
    """Alias for get_price"""
    return get_price(symbol, count, end_date, frequency, fields, skip_paused, fq)
```

#### 3. 引擎集成

```python
# engine/engine.py
from .context_local import set_context, clear_context

class StrategyExecutionEngine:
    def execute(self, exec_request):
        try:
            context = self._build_context(exec_request)
            
            # 设置 Context 到线程局部变量
            set_context(context)
            
            # 执行策略（策略代码中的 jqdatasdk.get_price() 可以访问 context）
            # ... 执行逻辑 ...
            
        finally:
            # 清理 Context
            clear_context()
```

### API 映射表

| JoinQuant API | 我们的实现 | 说明 |
|--------------|-----------|------|
| `jqdatasdk.get_price()` | `jqdata.get_price()` → `context.history()` | 返回 DataFrame |
| `jqdatasdk.get_bars()` | `jqdata.get_bars()` → `context.history()` | 返回 DataFrame |
| `jqdatasdk.get_fundamentals()` | 暂不支持 | 需要扩展 |
| `jqdatasdk.get_trade_days()` | 暂不支持 | 需要扩展 |
| `jqdatasdk.get_all_securities()` | 暂不支持 | 需要扩展 |

**优先级**：
1. **P0**：`get_price()`, `get_bars()` - 最常用
2. **P1**：`get_fundamentals()` - 基本面数据（如需要）
3. **P2**：其他辅助 API - 根据需求逐步添加

### 数据范围限制说明

由于我们的框架是无状态的，数据通过 ExecRequest 传递，因此：

1. **数据范围受限于 ExecRequest**：只能访问 ExecRequest 中提供的历史数据
2. **实时性**：数据是快照数据，不是实时查询
3. **警告机制**：如果请求的数据量超过可用数据，记录警告但不报错

**用户感知**：
- 在文档中明确说明数据范围限制
- 运行时记录警告（如果请求数据超出范围）
- 提供 `get_available_data_range()` 方法查询可用数据范围

## Migration Strategy

### 阶段 1：核心 API 实现（P0）

1. 实现线程局部存储机制
2. 创建 `jqdata.py` 兼容模块
3. 实现 `get_price()` 和 `get_bars()` API
4. 实现 DataFrame 转换
5. 引擎集成（设置/清理 Context）

### 阶段 2：扩展 API（P1）

1. 实现 `get_fundamentals()`（如需要）
2. 实现其他常用 API
3. 完善参数兼容性

### 阶段 3：文档和工具

1. 编写零代码迁移指南
2. 提供 API 映射文档
3. 创建迁移示例策略
4. 提供迁移检查工具（可选）

## Open Questions

1. **模块命名**：使用 `jqdata` 还是 `jqdatasdk`？
   - **建议**：同时支持两者，或使用 `jqdata`（更简洁）

2. **不支持的 API**：如何处理 JoinQuant 中我们暂不支持的 API？
   - **建议**：抛出明确的 NotImplementedError，并提供替代方案说明

3. **参数兼容性**：如何处理 JoinQuant 特有的参数（如 `fq`, `skip_paused`）？
   - **建议**：接受参数但不处理，或记录警告

4. **性能影响**：DataFrame 转换的性能开销？
   - **建议**：提供缓存机制，或允许直接返回 Bar 列表（通过参数控制）

5. **并发安全**：多线程执行时的 Context 隔离？
   - **建议**：使用 thread-local storage 确保线程安全

