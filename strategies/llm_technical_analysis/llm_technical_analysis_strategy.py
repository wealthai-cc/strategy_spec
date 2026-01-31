"""
LLM 技术分析策略

使用 crypto_technical_analysis 模板进行技术指标分析，并根据 LLM 分析结果进行交易决策。
"""

from typing import List
import logging
import pandas as pd
from strategy_spec.strategy import Strategy
from strategy_spec.objects import Context, Bar, Tick, Order, OrderOp, OrderType


class LLMTechnicalAnalysisStrategy(Strategy):
    """
    LLM 技术分析策略
    
    策略逻辑:
    1. 获取历史K线数据并计算技术指标
    2. 调用 LLM (crypto_technical_analysis 模板) 进行技术分析
    3. 根据 LLM 分析结果生成买卖信号
    4. 执行交易操作
    """
    
    def on_init(self, context: Context):
        # 配置 Logger 格式
        fmt = '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s'
        formatter = logging.Formatter(fmt)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            for handler in self.logger.handlers:
                handler.setFormatter(formatter)
        
        self.logger.propagate = False
        
        # 从配置读取参数
        self.symbol = context.strategy_params.get("symbol", "BTC/USDT")
        self.quantity = float(context.strategy_params.get("quantity", 0.01))
        
        # 技术指标参数
        self.ma_short = int(context.strategy_params.get("ma_short", 5))
        self.ma_long = int(context.strategy_params.get("ma_long", 20))
        self.rsi_period = int(context.strategy_params.get("rsi_period", 14))
        
        # MACD 参数
        self.macd_fast = int(context.strategy_params.get("macd_fast", 12))
        self.macd_slow = int(context.strategy_params.get("macd_slow", 26))
        self.macd_signal = int(context.strategy_params.get("macd_signal", 9))
        
        # 布林带参数
        self.bb_period = int(context.strategy_params.get("bb_period", 20))
        self.bb_std = float(context.strategy_params.get("bb_std", 2.0))
        
        # 策略状态
        self.current_pos = 0.0
        
        self.logger.info(f"LLMTechnicalAnalysisStrategy Initialized: {self.symbol}, "
                        f"Qty={self.quantity}, MA={self.ma_short}/{self.ma_long}, "
                        f"RSI={self.rsi_period}, MACD={self.macd_fast}/{self.macd_slow}/{self.macd_signal}, "
                        f"BB={self.bb_period}/{self.bb_std}")
    
    def on_start(self, context: Context):
        self.logger.info("LLMTechnicalAnalysisStrategy Started")
        
        # 从 Context 更新参数
        self.symbol = context.strategy_params.get("symbol", self.symbol)
        self.quantity = float(context.strategy_params.get("quantity", self.quantity))
        
        self.logger.info(f"Strategy Params Updated: Symbol={self.symbol}, Quantity={self.quantity}")
    
    def on_stop(self, context: Context):
        self.logger.info("LLMTechnicalAnalysisStrategy Stopped")
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> dict:
        """
        计算技术指标
        
        Returns:
            包含各种技术指标的字典
        """
        indicators = {}
        
        # 计算移动平均线
        df['ma_short'] = df['close'].rolling(window=self.ma_short).mean()
        df['ma_long'] = df['close'].rolling(window=self.ma_long).mean()
        
        # 计算 RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 计算 MACD
        exp1 = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.macd_signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 计算布林带
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        
        # 获取最新值
        latest = df.iloc[-1]
        
        indicators = {
            "current_price": float(latest['close']),
            "ma_short": float(latest['ma_short']) if pd.notna(latest['ma_short']) else None,
            "ma_long": float(latest['ma_long']) if pd.notna(latest['ma_long']) else None,
            "rsi": float(latest['rsi']) if pd.notna(latest['rsi']) else None,
            "macd": float(latest['macd']) if pd.notna(latest['macd']) else None,
            "macd_signal": float(latest['macd_signal']) if pd.notna(latest['macd_signal']) else None,
            "macd_hist": float(latest['macd_hist']) if pd.notna(latest['macd_hist']) else None,
            "bb_upper": float(latest['bb_upper']) if pd.notna(latest['bb_upper']) else None,
            "bb_middle": float(latest['bb_middle']) if pd.notna(latest['bb_middle']) else None,
            "bb_lower": float(latest['bb_lower']) if pd.notna(latest['bb_lower']) else None,
            "volume": float(latest['volume']) if pd.notna(latest['volume']) else None,
        }
        
        return indicators
    
    def _parse_llm_signal(self, code_blocks: List) -> str:
        """
        解析 LLM 返回的代码块，提取交易信号
        
        Returns:
            "buy", "sell", 或 "hold"
        """
        if not code_blocks:
            return "hold"
        
        # 将代码块转换为字符串进行分析
        analysis_text = " ".join([str(block) for block in code_blocks]).lower()
        
        # 查找明确的买卖信号
        buy_keywords = ["买入", "buy", "做多", "long", "看涨", "bullish", "建议买入"]
        sell_keywords = ["卖出", "sell", "做空", "short", "看跌", "bearish", "建议卖出"]
        
        buy_score = sum(1 for keyword in buy_keywords if keyword in analysis_text)
        sell_score = sum(1 for keyword in sell_keywords if keyword in analysis_text)
        
        if buy_score > sell_score and buy_score > 0:
            return "buy"
        elif sell_score > buy_score and sell_score > 0:
            return "sell"
        else:
            return "hold"
    
    def on_bar(self, context: Context, bar: Bar) -> List[OrderOp]:
        """
        当新的 Bar 到达时，使用 LLM 进行技术分析并生成交易信号
        """
        ops = []
        
        try:
            # 1. 获取历史K线数据
            ktype = bar.interval.to_ktype()
            if ktype == "":
                self.logger.warning(f"Invalid ktype: {ktype}")
                return []
            
            # 需要足够的数据来计算技术指标（取所有指标的最大周期）
            limit = max(self.ma_long, self.rsi_period, self.macd_slow, self.bb_period) + 10
            code, df = self.sdk.get_history_kline(self.symbol, max_count=limit, ktype=ktype)
            
            if code != 0:
                self.logger.error(f"Failed to get history kline, code: {code}")
                return []
            
            if df is None or len(df) < limit:
                self.logger.info(f"Insufficient data, required {limit} bars, got {len(df) if df is not None else 0} bars")
                return []
            
            # 2. 计算技术指标
            indicators = self._calculate_technical_indicators(df)
            
            # 3. 准备 LLM 调用参数
            params = {
                "symbol": self.symbol,
                "current_price": indicators["current_price"],
                "ma_short": indicators["ma_short"],
                "ma_long": indicators["ma_long"],
                "rsi": indicators["rsi"],
                "macd": indicators["macd"],
                "macd_signal": indicators["macd_signal"],
                "macd_hist": indicators["macd_hist"],
                "bb_upper": indicators["bb_upper"],
                "bb_middle": indicators["bb_middle"],
                "bb_lower": indicators["bb_lower"],
                "volume": indicators["volume"],
                "timestamp": bar.timestamp.isoformat() if hasattr(bar.timestamp, 'isoformat') else str(bar.timestamp),
            }
            
            # 4. 调用 LLM 进行技术分析
            self.logger.info(f"调用 LLM 技术分析模板分析 {self.symbol}...")
            result = self.sdk.call_llm(
                context=context,
                template_id="crypto_technical_analysis",
                params=params,
                timeout=30
            )
            
            # 5. 处理 LLM 返回结果
            code_blocks = result.get('code_blocks', [])
            if code_blocks:
                self.logger.info(f"LLM 返回了 {len(code_blocks)} 个代码块")
                for i, block in enumerate(code_blocks, 1):
                    # 记录代码块类型和内容摘要
                    block_type = block.get('type', 'unknown') if isinstance(block, dict) else 'text'
                    content = block.get('content', str(block)) if isinstance(block, dict) else str(block)
                    self.logger.debug(f"代码块 {i} (type={block_type}): {content[:100]}...")
            
            # 6. 解析交易信号
            signal = self._parse_llm_signal(code_blocks)
            self.logger.info(f"LLM 分析信号: {signal.upper()}")
            
            # 7. 获取当前持仓
            pos = context.portfolio.positions.get(self.symbol, None)
            if pos:
                self.current_pos = pos.available_volume
            else:
                self.logger.warning(f"Failed to get position for {self.symbol}")
                return []
            
            # 8. 根据信号执行交易
            current_price = float(bar.close)
            
            if signal == "buy" and self.current_pos == 0:
                # 买入信号且当前无持仓
                self.logger.info(f"执行买入: {self.symbol} @ {current_price}, 数量: {self.quantity}")
                op = self.buy(context, self.symbol, current_price, self.quantity, OrderType.MARKET_ORDER_TYPE)
                ops.append(op)
            
            elif signal == "sell" and self.current_pos > 0:
                # 卖出信号且当前有持仓
                sell_quantity = min(self.quantity, self.current_pos)
                self.logger.info(f"执行卖出: {self.symbol} @ {current_price}, 数量: {sell_quantity}")
                op = self.sell(context, self.symbol, current_price, sell_quantity, OrderType.MARKET_ORDER_TYPE)
                ops.append(op)
            
            elif signal == "hold":
                self.logger.debug("LLM 建议持有，不执行交易")
            
            return ops
            
        except Exception as e:
            self.logger.error(f"Error in on_bar: {e}", exc_info=True)
            return []
    
    def on_tick(self, context: Context, tick: Tick) -> List[OrderOp]:
        """Tick 数据触发（本策略不使用）"""
        return []
    
    def on_timer(self, context: Context) -> List[OrderOp]:
        """定时器触发（本策略不使用）"""
        return []
    
    def on_order_status(self, context: Context, order: Order) -> List[OrderOp]:
        """订单状态更新回调"""
        self.logger.info(f"Order Update: ID={order.order_id}, Status={order.status}, "
                        f"Filled={order.executed_size}")
        return []
