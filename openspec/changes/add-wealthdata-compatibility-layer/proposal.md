# Change: 添加 wealthdata 兼容层（JoinQuant 零代码迁移）

## Why

JoinQuant 平台使用 `jqdata`（jqdatasdk）作为数据访问接口，用户编写的策略代码大量使用 `jqdatasdk.get_price()`, `jqdatasdk.get_bars()` 等模块级 API。为了吸引 JoinQuant 用户平滑迁移到我们的平台，需要提供 `wealthdata` 兼容模块，让用户能够：

1. **直接复制 JoinQuant 策略代码**，无需修改业务逻辑
2. **保持原有语法**，支持 `jqdatasdk.get_price()` 等调用方式
3. **最小化修改**，只需替换 `import jqdatasdk` 为 `import wealthdata`，其他代码完全不变

**核心目标**：实现零代码修改的平滑迁移体验，用户只需修改一行 import 语句。

## What Changes

- **ADDED**: `wealthdata` 兼容模块（支持直接 import，替代 jqdata/jqdatasdk）
- **ADDED**: 模块级 API 函数（`get_price()`, `get_bars()` 等，与 jqdata 接口一致）
- **ADDED**: Context 对象的线程局部存储机制（Thread-local storage）
- **ADDED**: DataFrame 格式自动转换（Bar → pandas DataFrame）
- **ADDED**: JoinQuant 常用 API 映射（get_price, get_bars 等）
- **MODIFIED**: 策略执行引擎，在执行前设置 Context 到线程局部变量
- **ADDED**: 策略开发规范中说明 wealthdata 兼容层使用方式

**Non-Breaking**: 现有 API 保持不变，兼容层作为可选扩展

**关键特性**：
- 用户可以直接复制 JoinQuant 代码，只需修改一行 import：`import jqdatasdk` → `import wealthdata`
- 支持 `wealthdata.get_price()` 等模块级函数调用（与 jqdatasdk 接口完全一致）
- 自动将数据转换为 pandas DataFrame 格式（与 jqdata 返回格式一致）
- 内部映射到我们的 `context.history()` 方法，基于 ExecRequest 中的数据

## Impact

- **Affected specs**: 
  - `strategy-development` - 添加 wealthdata 兼容模块说明和使用示例
  - `python-sdk` - 可能需要扩展数据访问接口以支持 DataFrame 转换
  - `strategy-engine` - 添加 Context 线程局部存储机制说明
- **Affected code**: 
  - 新增 `wealthdata.py` 兼容模块
  - 引擎在执行策略前设置 Context 到线程局部变量
  - Context 对象扩展（可选，添加 jqdata 风格方法）
- **Affected docs**: 
  - 添加 JoinQuant 零代码迁移指南
  - 添加 wealthdata API 文档
  - 添加 API 对比表（jqdata vs wealthdata）

## Design Considerations

### JoinQuant jqdata 使用方式

JoinQuant 用户典型的代码模式：

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
- 使用 `jqdatasdk` 模块级函数（不是 context 方法）
- 返回 pandas DataFrame
- 支持 `count`, `frequency`, `end_date` 等参数
- 数据格式为 DataFrame，包含 `open`, `high`, `low`, `close`, `volume` 等列

### 我们的框架特点

当前框架使用方式：

```python
def initialize(context):
    context.symbol = 'BTCUSDT'

def handle_bar(context, bar):
    # Context 方法调用
    bars = context.history(context.symbol, 20, '1h')
    # bars 是 Bar 对象列表
    ma = sum(float(b.close) for b in bars) / len(bars)
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)
```

**关键特点**：
- 使用 `context.history()` 方法
- 返回 Bar 对象列表
- 数据来自 ExecRequest，范围受限

### 兼容方案：wealthdata 模块

提供 `wealthdata` 模块，实现与 `jqdatasdk` 相同的接口：

```python
# 用户代码（JoinQuant 代码，只需修改 import）
import wealthdata  # 原来是 import jqdatasdk

def initialize(context):
    context.symbol = 'BTCUSDT'  # 只改交易品种格式

def handle_bar(context, bar):
    # 其他代码完全不变！
    df = wealthdata.get_price(context.symbol, count=20, frequency='1h')
    ma = df['close'].mean()
    
    if float(bar.close) > ma:
        context.order_buy(context.symbol, 0.1)  # 下单 API 可能需要调整
```

**实现原理**：
1. `wealthdata` 模块通过线程局部变量访问当前执行的 Context
2. `wealthdata.get_price()` 内部调用 `context.history()`
3. 将 Bar 对象列表转换为 pandas DataFrame
4. 返回与 jqdata 相同格式的 DataFrame

### 核心差异对比

| 维度 | JoinQuant jqdata | 我们的 wealthdata | 兼容性 |
|------|-----------------|-----------------|--------|
| Import | `import jqdatasdk` | `import wealthdata` | ✅ 只需改一行 |
| API 调用 | `jqdatasdk.get_price()` | `wealthdata.get_price()` | ✅ 接口完全一致 |
| 返回格式 | pandas DataFrame | pandas DataFrame | ✅ 格式一致 |
| 数据来源 | 主动查询数据库 | 基于 ExecRequest 快照 | ⚠️ 数据范围受限 |
| 参数支持 | `count`, `frequency`, `end_date` | `count`, `frequency` (end_date 受限) | ⚠️ 部分参数受限 |

## Migration Strategy

### 阶段 1：wealthdata 模块实现

1. 创建 `wealthdata.py` 模块
2. 实现线程局部存储机制（Context 访问）
3. 实现 `get_price()`, `get_bars()` 等核心 API
4. 实现 Bar → DataFrame 转换

### 阶段 2：引擎集成

1. 引擎在执行策略前设置 Context 到线程局部变量
2. 引擎在执行后清理线程局部变量
3. 处理异常情况（Context 未设置等）

### 阶段 3：文档和示例

1. 编写 JoinQuant 迁移指南（零代码修改方案）
2. 提供 API 对比表
3. 创建迁移示例策略（展示直接复制代码的效果）
4. 说明数据范围限制和注意事项

## Open Questions

1. **模块命名**：使用 `wealthdata` 还是保持 `jqdata`/`jqdatasdk`？
   - **决策**：使用 `wealthdata`，明确标识是我们的兼容层，避免与原始 jqdata 混淆

2. **数据范围限制**：如何告知用户数据范围受限于 ExecRequest？
   - **建议**：在 API 文档中明确说明，运行时记录警告，提供 `get_available_data_range()` 方法

3. **API 覆盖度**：需要支持哪些 jqdata API？
   - **建议**：P0 - `get_price()`, `get_bars()`；P1 - `get_fundamentals()`；P2 - 其他 API

4. **向后兼容**：如何确保现有策略不受影响？
   - **建议**：新模块作为可选扩展，现有 `context.history()` API 保持不变

5. **线程安全**：如何确保并发执行时的线程安全？
   - **建议**：使用 `threading.local()` 实现线程局部存储，每个线程独立的 Context

6. **DataFrame 转换性能**：转换开销是否可接受？
   - **建议**：提供可选参数，允许直接返回 Bar 列表（高级用户），默认返回 DataFrame

