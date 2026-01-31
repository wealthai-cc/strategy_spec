# LLM 技术分析策略

使用 `crypto_technical_analysis` LLM 模板进行技术指标分析，并根据 AI 分析结果自动执行交易决策。

## 策略说明

### 功能特点

1. **技术指标计算**：
   - 移动平均线（MA）：短期和长期均线
   - RSI（相对强弱指标）
   - MACD（指数平滑移动平均线）
   - 布林带（Bollinger Bands）

2. **LLM 分析**：
   - 调用 `crypto_technical_analysis` 模板
   - 将技术指标数据传递给 LLM
   - 获取 AI 分析结果和交易建议

3. **自动交易**：
   - 根据 LLM 分析结果自动生成买卖信号
   - 支持买入、卖出、持有三种操作
   - 自动管理持仓，避免重复开仓

## 配置参数

在 `config.yaml` 中可以配置以下参数：

```yaml
params:
  symbol: "BTC/USDT"      # 交易标的
  quantity: 0.01          # 每次交易数量
  
  # 技术指标参数
  ma_short: 5             # 短期均线周期
  ma_long: 20             # 长期均线周期
  rsi_period: 14          # RSI 周期
```

## 运行方式

```bash
python run_strategy.py strategies/llm_technical_analysis/config.yaml
```

## 策略逻辑

1. **数据获取**：获取足够的历史K线数据（至少满足最长指标周期）
2. **指标计算**：计算 MA、RSI、MACD、布林带等技术指标
3. **LLM 分析**：将指标数据传递给 `crypto_technical_analysis` 模板
4. **信号解析**：从 LLM 返回的代码块中提取交易信号（买入/卖出/持有）
5. **执行交易**：根据信号和当前持仓情况执行交易操作

## 注意事项

- 策略需要 SDK 支持 `call_llm` 方法
- LLM 调用有超时限制（默认30秒）
- 策略会自动检查持仓，避免重复开仓
- 建议在实盘使用前充分测试
