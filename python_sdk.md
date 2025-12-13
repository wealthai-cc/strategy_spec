# Python SDK方法查询手册

## 分类：订单

### 方法：get_trading_rule
- 功能：查询指定 `broker + symbol` 的交易规则（TradingRule），用于下单参数合法性校验与风控计算
- 调用代价：本地读取与解析描述文件，无网络请求；典型毫秒级，带缓存为微秒级
- 参数：
  - `broker: str`：交易所/券商标识，如 `binance`、`okx`
  - `symbol: str`：交易品种标识，如 `BTCUSDT`、`ETHUSDT`
- 返回（示意字典/对象）：
  - `symbol`：品种代号
  - `min_quantity`：最小下单量
  - `quantity_step`：数量步进
  - `min_price`：最小价格
  - `price_tick`：价格最小变动单位
  - `price_precision`：价格精度（小数位数）
  - `quantity_precision`：数量精度（小数位数）
  - `max_leverage`：最大杠杆倍数（不适用则为默认值）
- 异常：
  - `NotFoundError`：本地无 `broker+symbol` 对应描述
  - `ParseError`：描述文件存在但解析失败（字段缺失/格式错误）
- 示例（Python）：
```python
from wealthai_sdk import get_trading_rule

rule = get_trading_rule(broker="binance", symbol="BTCUSDT")
# 使用 rule 校验数量、价格精度、最小下单量等
min_qty = rule["min_quantity"]
price_precision = rule["price_precision"]
```
- 建议：
  - 命中后按 `broker+symbol` 缓存，环境变更或文件更新后主动刷新
  - 接口需线程安全，支持并发查询

### 方法：get_commission_rates
- 功能：查询指定 `broker + symbol` 的 Maker/Taker 佣金费率，用于成本估算与策略收益评估
- 调用代价：本地读取与解析描述文件，无网络请求；典型毫秒级，带缓存为微秒级
- 参数：
  - `broker: str`：交易所/券商标识，如 `binance`、`okx`
  - `symbol: str`：交易品种标识，如 `BTCUSDT`、`ETHUSDT`
- 返回（示意字典/对象）：
  - `maker_fee_rate`：Maker 手续费率（小数，如 `0.0002`）
  - `taker_fee_rate`：Taker 手续费率（小数，如 `0.0004`）
- 异常：
  - `NotFoundError`：本地无 `broker+symbol` 对应描述
  - `ParseError`：描述文件存在但解析失败（字段缺失/格式错误）
- 示例（Python）：
```python
from wealthai_sdk import get_commission_rates

fees = get_commission_rates(broker="binance", symbol="BTCUSDT")
maker = fees["maker_fee_rate"]
taker = fees["taker_fee_rate"]
```
- 建议：
  - 与 TradingRule 一致的缓存与并发安全策略

