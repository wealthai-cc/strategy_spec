"""
LLM 调用示例

演示如何在策略中使用 self.sdk.call_llm() 方法
"""

from typing import List
from strategy_spec.strategy import Strategy
from strategy_spec.objects import Context, Bar, OrderOp


class LLMStrategyExample(Strategy):
    """
    使用 LLM 的策略示例
    
    这个示例展示如何在策略中调用 LLM 来分析市场并生成交易信号
    """
    
    def on_init(self, context: Context):
        self.symbol = context.strategy_params.get('symbol', 'BTC/USDT')
        self.logger.info(f"LLM Strategy Initialized for {self.symbol}")
    
    def on_start(self, context: Context):
        self.logger.info("LLM Strategy Started")
    
    def on_stop(self, context: Context):
        self.logger.info("LLM Strategy Stopped")
    
    def on_bar(self, context: Context, bar: Bar) -> List[OrderOp]:
        """
        使用 LLM 分析市场并生成交易信号
        """
        ops = []
        
        try:
            # 1. 准备 LLM 调用参数
            params = {
                "symbol": self.symbol,
                "current_price": float(bar.close),
                "volume": float(bar.volume),
                "timestamp": bar.timestamp.isoformat() if hasattr(bar.timestamp, 'isoformat') else str(bar.timestamp),
            }
            
            # 2. 调用 LLM 分析市场
            self.logger.info(f"调用 LLM 分析 {self.symbol} 的市场情况...")
            result = self.sdk.call_llm(
                context=context,
                template_id="market_analysis",  # 模板ID
                params=params,
                timeout=30  # 30秒超时
            )
            
            # 3. 处理 LLM 返回结果
            code_blocks = result.get('code_blocks', [])
            if code_blocks:
                self.logger.info(f"LLM 返回了 {len(code_blocks)} 个代码块")
                for i, code_block in enumerate(code_blocks):
                    self.logger.debug(f"代码块 {i+1}: {code_block[:100]}...")  # 只显示前100字符
            
            # 4. 根据 LLM 分析结果生成交易信号
            # 这里可以根据 code_blocks 中的内容来决定是否交易
            # 例如：如果 LLM 返回 "买入" 信号，则执行买入操作
            
            # 示例：如果 LLM 返回的代码块包含 "buy" 关键字，则买入
            should_buy = any("buy" in str(cb).lower() for cb in code_blocks)
            should_sell = any("sell" in str(cb).lower() for cb in code_blocks)
            
            if should_buy:
                self.logger.info("LLM 建议买入，执行买入操作")
                op = self.buy(context, self.symbol, float(bar.close), 0.01)
                ops.append(op)
            elif should_sell:
                self.logger.info("LLM 建议卖出，执行卖出操作")
                op = self.sell(context, self.symbol, float(bar.close), 0.01)
                ops.append(op)
            else:
                self.logger.info("LLM 未给出明确的交易信号")
            
        except Exception as e:
            self.logger.error(f"LLM 调用失败: {e}", exc_info=True)
        
        return ops
    
    def on_tick(self, context: Context, tick) -> List[OrderOp]:
        return []
    
    def on_order_status(self, context: Context, order) -> List[OrderOp]:
        return []
    
    def on_timer(self, context: Context) -> List[OrderOp]:
        return []
