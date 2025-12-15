# 账户与持仓规范

## 背景及目标

### 背景

账户与持仓是量化策略执行的基础数据结构，需要准确反映账户的资金状况、持仓信息以及风控指标。通过标准化的账户数据结构，确保策略在不同运行环境（回测、仿真、真实交易）中能够一致地访问账户信息。

### 目标

- **统一账户模型**：支持模拟账户、现金账户、保证金账户等多种账户类型
- **多币种支持**：支持 USDT、USDC、USD、HKD 等多种货币类型
- **完整持仓信息**：提供持仓数量、成本价、盈亏、保证金等完整信息
- **风控指标**：实时计算并传递保证金率、风险度、杠杆等风控指标
- **精度保证**：使用 Currency 结构保证金额计算的精度

## 使用场景/用户故事

### 场景 1：查询账户余额

**用户故事**：策略需要查询账户可用资金，以决定是否可以开仓或加仓。

**流程**：
1. 策略从 `ExecRequest.account` 获取账户信息
2. 遍历 `balances[]` 查找目标货币（如 USDT）
3. 读取 `free` 字段获取可用余额
4. 根据可用余额和价格计算可买入数量

### 场景 2：检查持仓信息

**用户故事**：策略需要检查当前持仓，以决定是否需要平仓或调整仓位。

**流程**：
1. 策略从 `ExecRequest.account.positions[]` 获取持仓列表
2. 根据 `symbol` 和 `position_side` 查找目标持仓
3. 读取 `quantity`、`average_cost_price`、`unrealized_pnl` 等信息
4. 根据持仓信息做出交易决策

### 场景 3：风控检查

**用户故事**：策略需要检查账户风险度，当风险度过高时采取风控措施。

**流程**：
1. 策略从 `ExecRequest.account` 读取风控指标
2. 检查 `risk_level`、`margin_ratio`、`available_margin` 等指标
3. 当风险度超过阈值时，触发减仓或平仓操作

## 接口/数据结构定义

### 账户类型（AccountType）

```protobuf
enum AccountType {
    INVALID_ACCOUNT_TYPE = 0;
    SIMULATE_ACCOUNT_TYPE = 1;  // 模拟交易专用账户（可支持保证金操作）
    CASH_ACCOUNT_TYPE = 2;      // 现金账户
    MARGIN_ACCOUNT_TYPE = 3;    // 保证金账户
}
```

### 货币类型（CurrencyType）

```protobuf
enum CurrencyType {
    INVALID_CURRENCY_TYPE = 0;
    USDT_CURRENCY_TYPE = 1;  // USDT（泰达币）
    USDC_CURRENCY_TYPE = 2;  // USDC（Circle 稳定币）
    USD_CURRENCY_TYPE = 3;   // USD（美元）
    HKD_CURRENCY_TYPE = 4;   // HKD（港币）
}
```

### 货币（Currency）

```protobuf
message Currency {
    CurrencyType currency_type = 1;  // 货币品种
    double amount = 2;                // 货币数量
}
```

### 余额（Balance）

```protobuf
message Balance {
    Currency free = 1;    // 可用余额
    Currency locked = 2;   // 冻结余额（被下单、提现或保证金锁定）
}
```

### 持仓方向（PositionSide）

```protobuf
enum PositionSide {
    INVALID_POSITION_SIDE = 0;
    LONG_POSITION_SIDE = 1;   // 多头
    SHORT_POSITION_SIDE = 2;  // 空头
}
```

### 持仓（Position）

```protobuf
message Position {
    PositionSide position_side = 1;      // 持仓方向
    string symbol = 2;                    // 品种代号
    double quantity = 3;                  // 持仓数量
    Currency average_cost_price = 4;      // 平均持仓成本价
    Currency unrealized_pnl = 5;          // 未实现盈亏
    Currency realized_pnl = 6;            // 已实现盈亏
    Currency initial_margin = 7;          // 初始保证金
    Currency maintenance_margin = 8;      // 维持保证金
    Currency position_pnl = 9;            // 持仓盈亏
}
```

### 账户（Account）

```protobuf
message Account {
    string account_id = 1;                // 账户唯一标识（系统登记的账户ID）
    AccountType account_type = 2;         // 账户类型（模拟/现金/保证金）
    repeated Balance balances = 3;        // 账户余额明细（可用/冻结）
    repeated Position positions = 4;      // 账户持仓明细
    Currency total_net_value = 5;         // 总资产净值（NAV）
    Currency available_margin = 6;        // 可用保证金
    double margin_ratio = 7;              // 保证金率（维持保证金/总资产净值）
    double risk_level = 8;                // 风险度（0-100，越高越危险）
    double leverage = 9;                 // 当前使用的杠杆倍数
}
```

## 约束与注意事项

### 账户类型约束

1. **模拟账户**：`SIMULATE_ACCOUNT_TYPE` 用于回测和仿真环境，可支持保证金操作
2. **现金账户**：`CASH_ACCOUNT_TYPE` 仅支持现货交易，不支持杠杆
3. **保证金账户**：`MARGIN_ACCOUNT_TYPE` 支持杠杆交易，需要关注保证金率

### 货币精度

1. **金额字段**：所有金额字段使用 `Currency` 结构，包含货币类型和数量
2. **精度保证**：`double` 类型可能存在精度问题，建议在关键计算中使用字符串或 Decimal 类型
3. **货币一致性**：同一账户的余额、持仓成本价、盈亏等应使用相同的货币类型

### 余额计算

1. **可用余额**：`free` 表示可以立即使用的资金
2. **冻结余额**：`locked` 表示被订单、提现或保证金锁定的资金
3. **总余额**：总余额 = `free + locked`（同一货币类型）

### 持仓信息

1. **持仓数量**：`quantity` 为正数，方向由 `position_side` 决定
2. **成本价**：`average_cost_price` 为平均持仓成本，用于计算盈亏
3. **盈亏计算**：
   - `unrealized_pnl`：未实现盈亏（基于当前市价）
   - `realized_pnl`：已实现盈亏（已平仓部分的盈亏）
   - `position_pnl`：持仓盈亏（总盈亏）

### 风控指标

1. **保证金率**：`margin_ratio = 维持保证金 / 总资产净值`
   - 保证金率越高，风险越大
   - 当保证金率接近 1.0 时，可能触发强制平仓
2. **风险度**：`risk_level` 范围 0-100
   - 0-50：低风险
   - 50-80：中风险
   - 80-100：高风险（可能触发风控措施）
3. **可用保证金**：`available_margin` 表示可用于开仓的保证金
4. **杠杆倍数**：`leverage` 表示当前使用的杠杆倍数

## 示例与用例

### 示例 1：查询 USDT 可用余额

```python
# 从 ExecRequest 获取账户信息
account = exec_request.account

# 查找 USDT 余额
usdt_balance = None
for balance in account.balances:
    if balance.free.currency_type == CurrencyType.USDT_CURRENCY_TYPE:
        usdt_balance = balance.free.amount
        break

if usdt_balance and usdt_balance > 1000:
    # 可用余额大于 1000 USDT，可以开仓
    pass
```

### 示例 2：检查 BTCUSDT 持仓

```python
# 查找 BTCUSDT 多头持仓
btc_position = None
for position in account.positions:
    if position.symbol == "BTCUSDT" and position.position_side == PositionSide.LONG_POSITION_SIDE:
        btc_position = position
        break

if btc_position:
    print(f"持仓数量: {btc_position.quantity}")
    print(f"成本价: {btc_position.average_cost_price.amount}")
    print(f"未实现盈亏: {btc_position.unrealized_pnl.amount}")
```

### 示例 3：风控检查

```python
# 检查账户风险度
if account.risk_level > 80:
    # 风险度过高，需要减仓
    print(f"风险度: {account.risk_level}%，需要减仓")
    
if account.margin_ratio > 0.9:
    # 保证金率过高，接近强制平仓
    print(f"保证金率: {account.margin_ratio}，接近强制平仓线")
    
if account.available_margin.amount < 100:
    # 可用保证金不足
    print(f"可用保证金: {account.available_margin.amount}，不足")
```

### 示例 4：计算可买入数量

```python
# 获取可用余额
usdt_balance = get_balance(account, CurrencyType.USDT_CURRENCY_TYPE)

# 获取当前价格（从 market_data_context）
current_price = float(market_data_context.bars[-1].close)

# 计算可买入数量（保留 10% 作为缓冲）
available_amount = usdt_balance * 0.9
buyable_quantity = available_amount / current_price

# 考虑最小下单量和精度
trading_rule = get_trading_rule("binance", "BTCUSDT")
min_quantity = trading_rule["min_quantity"]
quantity_step = trading_rule["quantity_step"]

# 调整数量
buyable_quantity = max(buyable_quantity, min_quantity)
buyable_quantity = round(buyable_quantity / quantity_step) * quantity_step
```

## Q&A、FAQ

### Q1：如何区分不同货币的余额？

**A**：遍历 `balances[]` 数组，通过 `Currency.currency_type` 字段区分。每个 `Balance` 对象对应一种货币类型。

### Q2：持仓数量可以为负数吗？

**A**：不可以。`quantity` 始终为正数，持仓方向由 `position_side` 字段决定。多头持仓用 `LONG_POSITION_SIDE`，空头持仓用 `SHORT_POSITION_SIDE`。

### Q3：如何计算总资产净值？

**A**：`total_net_value` 由系统计算并传递，包含：
- 所有货币的余额（可用 + 冻结）
- 所有持仓的市值
- 已实现盈亏

策略不应自行计算，应直接使用系统提供的值。

### Q4：保证金账户和现金账户的区别？

**A**：
- **现金账户**：只能使用自有资金交易，不支持杠杆，`leverage = 1.0`
- **保证金账户**：可以使用杠杆交易，`leverage > 1.0`，需要关注保证金率和风险度

### Q5：如何判断账户是否需要补充保证金？

**A**：检查以下指标：
1. `risk_level > 80`：风险度过高
2. `margin_ratio > 0.9`：保证金率过高
3. `available_margin.amount < 0`：可用保证金为负

当满足以上条件时，系统可能触发 `RISK_MANAGE_TRIGGER_TYPE` 风控事件。

---

**相关文档**：
- [策略执行引擎规范](../strategy-engine/spec.md)
- [订单管理规范](../order/spec.md)

