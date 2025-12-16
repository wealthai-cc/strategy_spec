# Change: 设计 JoinQuant 兼容层

## Why

JoinQuant 平台使用 `jqdata`（jqdatasdk）作为数据访问接口，提供了类似 `get_price()`, `get_fundamentals()` 等 API。我们的框架使用 `context.history()` 方法获取历史数据，API 风格不同。

为了吸引 JoinQuant 用户迁移到我们的平台，需要提供兼容层，让 JoinQuant 策略代码能够平滑迁移，减少代码修改成本。

## What Changes

- **ADDED**: JoinQuant 兼容层设计（API 映射和适配器）
- **ADDED**: jqdata/jqdatasdk 模块兼容层（支持直接 import，无需修改代码）
- **ADDED**: jqdata 风格的 Context 扩展接口
- **ADDED**: 数据访问 API 兼容性（get_price, get_bars 等）
- **ADDED**: 策略迁移指南和工具
- **MODIFIED**: Context 对象扩展，支持 JoinQuant 风格的 API

**Non-Breaking**: 现有 API 保持不变，兼容层作为可选扩展

**关键特性**：支持直接复制 JoinQuant 策略代码，只需替换 `import jqdatasdk` 为 `import jqdata`（我们的兼容模块），其他代码无需修改。

## Impact

- **Affected specs**: 
  - `strategy-development` - 添加 JoinQuant 兼容 API 说明
  - `python-sdk` - 可能需要扩展数据访问接口
- **Affected code**: 
  - Context 对象扩展（添加 jqdata 风格方法）
  - 可选的数据访问适配器
  - 策略迁移工具和文档
- **Affected docs**: 
  - 添加 JoinQuant 迁移指南
  - 添加 API 对比文档
  - 添加兼容性说明

## Design Considerations

### JoinQuant jqdata 特点

1. **数据访问方式**：
   - `jqdatasdk.get_price()` - 获取价格数据
   - `jqdatasdk.get_bars()` - 获取 K 线数据
   - `jqdatasdk.get_fundamentals()` - 获取基本面数据
   - 支持 pandas DataFrame 返回格式

2. **策略执行环境**：
   - 在线平台执行，数据通过 SDK 调用获取
   - 策略代码在云端运行
   - 数据访问是主动拉取模式

### 我们的框架特点

1. **数据访问方式**：
   - `context.history()` - 获取历史 K 线数据
   - 数据通过 ExecRequest 被动传递
   - 返回 Bar 对象列表

2. **策略执行环境**：
   - 无状态执行，每次 Exec 调用传入完整上下文
   - 数据在 ExecRequest 中预先准备好
   - 数据访问是被动接收模式

### 核心差异

| 维度 | JoinQuant jqdata | 我们的框架 |
|------|-----------------|-----------|
| 数据获取 | 主动调用 API (`get_price()`) | 被动接收 (`context.history()`) |
| 数据格式 | pandas DataFrame | Bar 对象列表 |
| 数据范围 | 可查询任意历史数据 | 受限于 ExecRequest 中的数据 |
| 实时性 | 实时查询最新数据 | 基于传入的快照数据 |
| 执行模式 | 有状态（策略保持运行） | 无状态（每次 Exec 独立） |

### 兼容方案

#### 方案 1：API 适配层（推荐）

在 Context 对象上提供 jqdata 风格的 API，内部映射到我们的数据访问方式：

```python
# JoinQuant 风格
context.get_price('BTCUSDT', count=20, end_date=None, frequency='1h')

# 映射到我们的 API
context.history('BTCUSDT', 20, '1h')
```

**优点**：
- 代码修改最小
- 保持 API 语义一致
- 易于理解和迁移

**缺点**：
- 数据范围受限于 ExecRequest
- 需要处理 DataFrame 转换

#### 方案 2：数据格式转换

提供工具函数将我们的 Bar 对象列表转换为 pandas DataFrame：

```python
# 我们的数据格式
bars = context.history('BTCUSDT', 20, '1h')

# 转换为 DataFrame
df = context.to_dataframe(bars)
```

**优点**：
- 保持数据格式兼容
- 支持现有 pandas 分析代码

**缺点**：
- 需要额外转换步骤
- 性能开销

#### 方案 3：混合方案（最佳）

结合方案 1 和 2：
- 提供 jqdata 风格的 API（`get_price`, `get_bars`）
- 自动转换为 DataFrame 格式
- 保持向后兼容（现有 `history` API 继续可用）

#### 方案 4：jqdata 模块兼容层（新增，实现零代码修改）

提供 `jqdata` 或 `jqdatasdk` 兼容模块，让用户可以直接复制 JoinQuant 代码：

```python
# JoinQuant 原始代码（无需修改）
import jqdatasdk

def handle_bar(context, bar):
    df = jqdatasdk.get_price('BTCUSDT', count=20, frequency='1h')
    ma = df['close'].mean()
    # ... 其他代码完全不变
```

**实现方式**：
- 创建 `jqdata.py` 或 `jqdatasdk.py` 模块
- 模块内部访问当前执行的 Context 对象（通过线程局部变量或全局注册）
- 将 `jqdatasdk.get_price()` 等调用映射到 `context.get_price()`

**优点**：
- **零代码修改**：用户只需替换 import 语句
- **完全兼容**：支持所有 JoinQuant 代码语法
- **平滑迁移**：降低迁移成本

**缺点**：
- 需要管理 Context 对象的全局访问
- 需要处理线程安全问题（如果支持并发执行）

## Migration Strategy

### 阶段 1：API 兼容层

1. 在 Context 对象上添加 jqdata 风格方法
2. 实现数据格式转换（Bar → DataFrame）
3. 提供 API 映射文档

### 阶段 2：jqdata 模块兼容层（新增）

1. 创建 `jqdata` 或 `jqdatasdk` 兼容模块
2. 实现 Context 对象的全局访问机制（线程局部变量）
3. 实现 `get_price()`, `get_bars()` 等 API 映射
4. 处理模块级别的函数调用（如 `jqdatasdk.get_price()`）

### 阶段 3：迁移工具

1. 创建策略代码转换工具（自动替换 import）
2. 提供迁移检查清单
3. 编写迁移示例

### 阶段 4：文档和示例

1. 编写 JoinQuant 迁移指南（零代码修改方案）
2. 提供 API 对比表
3. 创建迁移示例策略（展示直接复制代码的效果）

## Open Questions

1. **数据范围限制**：如何告知用户数据范围受限于 ExecRequest？
   - **建议**：在 API 文档中明确说明，运行时记录警告

2. **性能影响**：DataFrame 转换的性能开销是否可接受？
   - **建议**：提供可选参数，允许直接返回 Bar 列表

3. **API 覆盖度**：需要支持哪些 jqdata API？
   - **建议**：优先支持最常用的（get_price, get_bars），其他逐步添加

4. **向后兼容**：如何确保现有策略不受影响？
   - **建议**：新 API 作为扩展，现有 API 保持不变

5. **jqdata 模块访问 Context**：如何在模块级别访问当前执行的 Context？
   - **建议**：使用线程局部变量（thread-local storage）存储当前 Context，引擎在执行策略前设置，执行后清理

6. **import 语句替换**：用户如何知道要替换 import？
   - **建议**：提供迁移工具自动替换，或在文档中明确说明只需修改一行 import

