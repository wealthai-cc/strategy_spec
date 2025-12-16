# WealthAI SDK 配置文件

## 目录结构

```
config/
├── trading_rules/          # 交易规则配置
│   ├── binance.json       # Binance 交易规则
│   └── okx.json           # OKX 交易规则（示例）
├── commission_rates/       # 佣金费率配置
│   ├── binance.json       # Binance 佣金费率
│   └── okx.json           # OKX 佣金费率（示例）
└── README.md              # 本文件
```

## 配置文件格式

### 交易规则文件 (trading_rules/*.json)

```json
{
  "SYMBOL": {
    "symbol": "交易品种代号",
    "min_quantity": "最小下单量（数字）",
    "quantity_step": "数量步进（数字）",
    "min_price": "最小价格（数字）",
    "price_tick": "价格最小变动单位（数字）",
    "price_precision": "价格精度-小数位数（整数）",
    "quantity_precision": "数量精度-小数位数（整数）",
    "max_leverage": "最大杠杆倍数（数字，可选，默认1.0）"
  }
}
```

### 佣金费率文件 (commission_rates/*.json)

```json
{
  "SYMBOL": {
    "maker_fee_rate": "Maker手续费率（小数，如0.0002表示0.02%）",
    "taker_fee_rate": "Taker手续费率（小数，如0.0004表示0.04%）"
  }
}
```

## 使用说明

1. **添加新交易所**：在对应目录下创建 `{broker}.json` 文件
2. **添加新品种**：在现有文件中添加新的 symbol 配置
3. **更新配置**：直接修改 JSON 文件，SDK 会自动重新加载

## 配置优先级

SDK 按以下优先级查找配置文件：

1. 环境变量 `WEALTHAI_CONFIG_DIR` 指定的目录
2. 项目根目录的 `config/` 目录
3. 用户主目录的 `.wealthai/` 目录

## 注意事项

- 所有数值字段必须是有效的数字格式
- JSON 文件必须符合标准格式，注意逗号和引号
- 文件编码必须是 UTF-8
- 修改配置文件后，缓存会在下次查询时自动更新