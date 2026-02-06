from typing import List, Optional
import logging
import pandas as pd
from strategy_spec.strategy import Strategy
from strategy_spec.objects import Context, Order, OrderType, Bar, Tick, OrderOp, DirectionType

class DualMAStrategy(Strategy):
    """
    双均线策略示例 (Dual Moving Average Strategy)
    
    逻辑:
    1. 短周期均线 (Short MA) 上穿 长周期均线 (Long MA) -> 买入 (Golden Cross)
    2. 短周期均线 (Short MA) 下穿 长周期均线 (Long MA) -> 卖出 (Death Cross)
    """

    def on_init(self, context: Context):
        # 配置 Logger 格式
        # 格式: 时间戳 - 日志等级 - 代码路径:行号 - 方法名 - 消息
        fmt = '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s'
        formatter = logging.Formatter(fmt)
        
        # 检查是否已有 Handler，避免重复添加
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            # 如果已有 Handler，更新其格式
            for handler in self.logger.handlers:
                handler.setFormatter(formatter)
                
        # 禁止传播，防止父级 Logger 重复输出
        self.logger.propagate = False

        self.symbol = "BTC/USDT"
        self.quantity = 0.01
        
        # 均线参数
        self.short_window = 5
        self.long_window = 10
        
        # 策略状态
        self.current_pos = 0.0 # 当前持仓数量
        
        self.logger.info(f"DualMAStrategy Initialized: {self.symbol}, Qty={self.quantity}, "
              f"Windows={self.short_window}/{self.long_window}")

    def on_start(self, context: Context):
        self.logger.info("DualMAStrategy Started")
        
        # 从 Context 更新参数 (如果在 ExecRequest 中指定了参数，这里会生效)
        self.short_window = int(context.strategy_params.get("short_window", self.short_window))
        self.long_window = int(context.strategy_params.get("long_window", self.long_window))
        
        self.logger.info(f"DualMAStrategy Params Updated: Windows={self.short_window}/{self.long_window}")

    def on_stop(self, context: Context):
        self.logger.info("DualMAStrategy Stopped")

    def on_bar(self, context: Context, bar: Bar) -> List[OrderOp]:
        """
        当新的 Bar (K线) 到达时调用。
        """
        # self.logger.debug(f"current bar: {bar}")
        try:
            if not self.sdk:
                self.logger.error("SDK not initialized")
                return []

            # Use TimeFrame.to_ktype() directly
            ktype = bar.interval.to_ktype()

            if ktype == "":
                self.logger.warning(f"Invalid ktype: {ktype}")
                return []

            # 1. 获取历史K线数据
            # 需要足够的长度来计算长周期均线 (至少 long_window + 1 个点用于判断交叉)
            limit = self.long_window + 5
            code, df = self.sdk.get_history_kline(self.symbol, max_count=limit, ktype=ktype)
            
            if code != 0:
                self.logger.error(f"Failed to get history kline, code: {code}")
                return []
            
            if df is None or len(df) < limit:
                self.logger.info(f"Insufficient data，required {limit} bars, got {len(df)} bars")   
                return []

            # 2. 计算均线
            # 假设 df 包含 'close' 列
            df['short_ma'] = df['close'].rolling(window=self.short_window).mean()
            df['long_ma'] = df['close'].rolling(window=self.long_window).mean()

            # 获取最后两个点的数据 (current 和 previous)
            curr = df.iloc[-1]
            prev = df.iloc[-2]

            # 3. 判断交叉信号
            
            # 金叉: 前一刻 Short <= Long, 当前 Short > Long
            golden_cross = (prev['short_ma'] <= prev['long_ma']) and (curr['short_ma'] > curr['long_ma'])
            
            # 死叉: 前一刻 Short >= Long, 当前 Short < Long
            death_cross = (prev['short_ma'] >= prev['long_ma']) and (curr['short_ma'] < curr['long_ma'])

            # 4. 执行交易
            # 这里简单演示: 金叉买入, 死叉卖出
            # 实际策略中可能需要检查当前持仓 (self.current_pos) 避免重复开仓
            
            pos = context.portfolio.positions.get(self.symbol, None)
            if pos:
                self.current_pos = pos.available_volume
            else:
                self.logger.error(f"Failed to get position for {self.symbol}")
                return []
            
            if golden_cross:
                self.logger.info(f"Signal: Golden Cross detected at {curr['close']}")
                self.logger.info(f"Action: Buying {self.quantity} {self.symbol}")
                order = Order(
                    symbol=self.symbol,
                    direction_type=DirectionType.BUY_DIRECTION_TYPE,
                    order_type=OrderType.MARKET_ORDER_TYPE,
                    size=str(self.quantity),
                    price=str(curr["close"]),
                )
                order_id = self.sdk.place_order(order)
                self.logger.info(f"Order placed: {order_id}")
            
            elif death_cross:
                self.logger.info(f"Signal: Death Cross detected at {curr['close']}")
                self.logger.info(f"Action: Selling {self.quantity} {self.symbol}")
                order = Order(
                    symbol=self.symbol,
                    direction_type=DirectionType.SELL_DIRECTION_TYPE,
                    order_type=OrderType.MARKET_ORDER_TYPE,
                    size=str(self.quantity),
                    price=str(curr["close"]),
                )
                order_id = self.sdk.place_order(order)
                self.logger.info(f"Order placed: {order_id}")
            
            return []

        except Exception as e:
            self.logger.error(f"Error in on_bar: {e}", exc_info=True)
            return []

    def on_tick(self, context: Context, tick: Tick) -> List[OrderOp]:
        return []

    def on_timer(self, context: Context) -> List[OrderOp]:
        """
        定时触发逻辑 (例如每分钟触发一次)
        """
        return []

    def on_order_status(self, context: Context, order: Order) -> List[OrderOp]:
        """
        订单状态更新回调
        """
        self.logger.info(f"Order Update: ID={order.order_id}, Status={order.status}, Filled={order.executed_size}")
        
        return []
