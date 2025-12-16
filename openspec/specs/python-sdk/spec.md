# Python SDK 规范

## 背景及目标

### 背景

Python SDK 为策略提供本地查询接口，用于获取交易规则和佣金费率等配置信息。这些接口通过本地文件读取实现，避免网络请求，提供毫秒级的响应速度。

### 目标

- **本地查询**：所有接口通过本地文件读取，无网络请求
- **高性能**：典型毫秒级响应，带缓存为微秒级
- **线程安全**：支持并发查询
- **缓存机制**：按 `broker+symbol` 缓存查询结果
- **错误处理**：提供明确的异常类型和处理方式

## 使用场景/用户故事

### 场景 1：下单前参数校验

**用户故事**：策略需要创建订单，在下单前需要校验数量、价格等参数是否符合交易所要求。

**流程**：
1. 策略调用 `get_trading_rule("binance", "BTCUSDT")` 获取交易规则
2. 检查订单数量是否 >= `min_quantity`
3. 检查数量是否符合 `quantity_step` 的整数倍
4. 检查价格精度是否符合 `price_precision` 要求
5. 调整订单参数后创建订单

### 场景 2：成本估算

**用户故事**：策略需要估算交易成本，以评估策略收益。

**流程**：
1. 策略调用 `get_commission_rates("binance", "BTCUSDT")` 获取佣金费率
2. 根据订单类型（Maker/Taker）选择对应的费率
3. 计算交易成本：`成本 = 成交金额 * 费率`
4. 在策略决策中考虑交易成本

### 场景 3：杠杆限制检查

**用户故事**：策略需要检查品种的最大杠杆倍数，避免超限。

**流程**：
1. 策略调用 `get_trading_rule("binance", "BTCUSDT")` 获取交易规则
2. 读取 `max_leverage` 字段
3. 检查策略使用的杠杆是否 <= `max_leverage`
4. 如果超限，调整杠杆或选择其他品种

## 接口/数据结构定义

### get_trading_rule

**功能**：查询指定 `broker + symbol` 的交易规则（TradingRule），用于下单参数合法性校验与风控计算

**调用代价**：本地读取与解析描述文件，无网络请求；典型毫秒级，带缓存为微秒级

**函数签名**：
```python
def get_trading_rule(broker: str, symbol: str) -> dict
```

**参数**：
- `broker: str`：交易所/券商标识，如 `binance`、`okx`
- `symbol: str`：交易品种标识，如 `BTCUSDT`、`ETHUSDT`

**返回**（字典/对象）：
- `symbol`：品种代号
- `min_quantity`：最小下单量
- `quantity_step`：数量步进（数量必须是该值的整数倍）
- `min_price`：最小价格
- `price_tick`：价格最小变动单位（价格必须是该值的整数倍）
- `price_precision`：价格精度（小数位数）
- `quantity_precision`：数量精度（小数位数）
- `max_leverage`：最大杠杆倍数（不适用则为默认值，如 1.0）

**异常**：
- `NotFoundError`：本地无 `broker+symbol` 对应描述
- `ParseError`：描述文件存在但解析失败（字段缺失/格式错误）

**示例**：
```python
from wealthai_sdk import get_trading_rule

try:
    rule = get_trading_rule(broker="binance", symbol="BTCUSDT")
    
    # 使用规则校验数量、价格精度、最小下单量等
    min_qty = rule["min_quantity"]
    price_precision = rule["price_precision"]
    quantity_step = rule["quantity_step"]
    
    # 调整订单数量
    target_qty = 0.123456789
    target_qty = max(target_qty, min_qty)  # 不小于最小数量
    target_qty = round(target_qty / quantity_step) * quantity_step  # 符合步进
    
except NotFoundError:
    print(f"未找到 {broker}/{symbol} 的交易规则")
except ParseError as e:
    print(f"解析交易规则失败: {e}")
```

### get_commission_rates

**功能**：查询指定 `broker + symbol` 的 Maker/Taker 佣金费率，用于成本估算与策略收益评估

**调用代价**：本地读取与解析描述文件，无网络请求；典型毫秒级，带缓存为微秒级

**函数签名**：
```python
def get_commission_rates(broker: str, symbol: str) -> dict
```

**参数**：
- `broker: str`：交易所/券商标识，如 `binance`、`okx`
- `symbol: str`：交易品种标识，如 `BTCUSDT`、`ETHUSDT`

**返回**（字典/对象）：
- `maker_fee_rate`：Maker 手续费率（小数，如 `0.0002` 表示 0.02%）
- `taker_fee_rate`：Taker 手续费率（小数，如 `0.0004` 表示 0.04%）

**异常**：
- `NotFoundError`：本地无 `broker+symbol` 对应描述
- `ParseError`：描述文件存在但解析失败（字段缺失/格式错误）

**示例**：
```python
from wealthai_sdk import get_commission_rates

try:
    fees = get_commission_rates(broker="binance", symbol="BTCUSDT")
    
    maker_rate = fees["maker_fee_rate"]  # 0.0002 (0.02%)
    taker_rate = fees["taker_fee_rate"]   # 0.0004 (0.04%)
    
    # 计算交易成本
    order_amount = 10000.0  # 订单金额
    if order_type == "LIMIT_ORDER_TYPE":
        commission = order_amount * maker_rate  # Maker 订单
    else:
        commission = order_amount * taker_rate  # Taker 订单
    
except NotFoundError:
    print(f"未找到 {broker}/{symbol} 的佣金费率")
except ParseError as e:
    print(f"解析佣金费率失败: {e}")
```

## 约束与注意事项

### 缓存机制

1. **缓存键**：使用 `broker+symbol` 作为缓存键
2. **缓存更新**：环境变更或文件更新后应主动刷新缓存
3. **缓存失效**：建议提供缓存失效机制，支持手动刷新

### 线程安全

1. **并发查询**：接口必须支持多线程并发查询
2. **线程安全实现**：使用线程安全的缓存机制（如 `threading.RLock`）
3. **性能考虑**：在保证线程安全的前提下，尽量减少锁竞争

### 错误处理

1. **NotFoundError**：当本地不存在对应的交易规则或佣金费率时抛出
   - 策略应检查 broker 和 symbol 是否正确
   - 可能需要等待配置文件更新

2. **ParseError**：当配置文件存在但格式错误时抛出
   - 策略应记录错误信息，便于排查
   - 可能需要联系管理员修复配置文件

3. **默认值处理**：某些字段可能不存在或为默认值
   - `max_leverage` 如果不适用，可能为 1.0
   - 策略应检查字段是否存在，提供默认处理逻辑

### 性能优化

1. **首次查询**：首次查询需要读取和解析文件，耗时可能为毫秒级
2. **缓存命中**：缓存命中后查询耗时降为微秒级
3. **批量查询**：如果需要查询多个品种，建议批量查询并缓存结果

### 数据精度

1. **费率精度**：费率使用小数表示，如 `0.0002` 表示 0.02%
2. **精度字段**：`price_precision` 和 `quantity_precision` 为整数，表示小数位数
3. **步进字段**：`price_tick` 和 `quantity_step` 为浮点数，表示最小变动单位

## 示例与用例

### 示例 1：下单前完整校验

```python
from wealthai_sdk import get_trading_rule
from decimal import Decimal

def validate_order_params(broker: str, symbol: str, price: float, quantity: float) -> tuple[bool, str]:
    """校验订单参数"""
    try:
        rule = get_trading_rule(broker, symbol)
    except NotFoundError:
        return False, f"未找到 {broker}/{symbol} 的交易规则"
    except ParseError as e:
        return False, f"解析交易规则失败: {e}"
    
    # 校验数量
    if quantity < rule["min_quantity"]:
        return False, f"数量 {quantity} 小于最小数量 {rule['min_quantity']}"
    
    if quantity % rule["quantity_step"] != 0:
        return False, f"数量 {quantity} 不符合步进 {rule['quantity_step']}"
    
    # 校验价格
    if price < rule["min_price"]:
        return False, f"价格 {price} 小于最小价格 {rule['min_price']}"
    
    # 校验价格精度
    price_str = f"{price:.{rule['price_precision']}f}"
    if float(price_str) != price:
        return False, f"价格精度不符合要求（应为 {rule['price_precision']} 位小数）"
    
    return True, "校验通过"

# 使用示例
is_valid, message = validate_order_params("binance", "BTCUSDT", 42000.0, 0.1)
if not is_valid:
    print(f"校验失败: {message}")
```

### 示例 2：调整订单数量

```python
from wealthai_sdk import get_trading_rule

def adjust_quantity(broker: str, symbol: str, target_qty: float) -> float:
    """调整订单数量，使其符合交易规则"""
    try:
        rule = get_trading_rule(broker, symbol)
    except (NotFoundError, ParseError):
        return target_qty  # 如果无法获取规则，返回原值
    
    min_qty = rule["min_quantity"]
    quantity_step = rule["quantity_step"]
    quantity_precision = rule["quantity_precision"]
    
    # 调整数量
    adjusted_qty = max(target_qty, min_qty)  # 不小于最小数量
    adjusted_qty = round(adjusted_qty / quantity_step) * quantity_step  # 符合步进
    adjusted_qty = round(adjusted_qty, quantity_precision)  # 符合精度
    
    return adjusted_qty

# 使用示例
target_qty = 0.123456789
adjusted_qty = adjust_quantity("binance", "BTCUSDT", target_qty)
print(f"原始数量: {target_qty}, 调整后: {adjusted_qty}")
```

### 示例 3：计算交易成本

```python
from wealthai_sdk import get_commission_rates

def calculate_commission(broker: str, symbol: str, order_type: str, amount: float) -> float:
    """计算交易佣金"""
    try:
        fees = get_commission_rates(broker, symbol)
    except (NotFoundError, ParseError):
        return 0.0  # 如果无法获取费率，返回 0
    
    if order_type == "LIMIT_ORDER_TYPE":
        rate = fees["maker_fee_rate"]
    else:
        rate = fees["taker_fee_rate"]
    
    return amount * rate

# 使用示例
order_amount = 10000.0
commission = calculate_commission("binance", "BTCUSDT", "LIMIT_ORDER_TYPE", order_amount)
print(f"订单金额: {order_amount}, 佣金: {commission}")
```

### 示例 4：检查杠杆限制

```python
from wealthai_sdk import get_trading_rule

def check_leverage(broker: str, symbol: str, target_leverage: float) -> tuple[bool, str]:
    """检查杠杆是否超限"""
    try:
        rule = get_trading_rule(broker, symbol)
    except (NotFoundError, ParseError):
        return True, "无法获取交易规则，跳过检查"
    
    max_leverage = rule.get("max_leverage", 1.0)
    
    if target_leverage > max_leverage:
        return False, f"杠杆 {target_leverage} 超过最大杠杆 {max_leverage}"
    
    return True, "杠杆检查通过"

# 使用示例
is_valid, message = check_leverage("binance", "BTCUSDT", 10.0)
if not is_valid:
    print(f"杠杆检查失败: {message}")
```

## Q&A、FAQ

### Q1：为什么使用本地文件而不是网络请求？

**A**：本地文件读取可以避免网络延迟和网络故障，提供更快的响应速度和更高的可靠性。交易规则和佣金费率相对稳定，适合本地缓存。

### Q2：配置文件在哪里？

**A**：配置文件的位置由 SDK 实现决定，通常位于策略运行环境的配置目录中。策略不需要关心配置文件的具体位置，只需调用接口即可。

### Q3：如何更新交易规则和佣金费率？

**A**：配置文件更新后，SDK 应提供缓存刷新机制。策略可以调用刷新接口，或等待缓存自动失效。具体实现方式由 SDK 决定。

### Q4：如果查询失败怎么办？

**A**：策略应根据异常类型采取不同的处理方式：
- `NotFoundError`：可能需要等待配置文件更新，或使用默认值
- `ParseError`：记录错误信息，联系管理员修复配置文件

### Q5：是否支持批量查询？

**A**：当前接口设计为单次查询。如果需要查询多个品种，建议在策略中循环调用，SDK 的缓存机制可以保证后续查询的高性能。

---

**相关文档**：
- [策略执行引擎规范](../strategy-engine/spec.md)
- [策略开发规范](../strategy-development/spec.md)
- [订单管理规范](../order/spec.md)

