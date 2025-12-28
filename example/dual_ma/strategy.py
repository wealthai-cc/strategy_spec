from typing import List, Optional
import pandas as pd
from strategy_spec.strategy import Strategy
from strategy_spec.objects import Context, Order, OrderStatusType, OrderType

class DualMAStrategy(Strategy):
    """
    双均线策略示例 (Dual Moving Average Strategy)
    
    逻辑:
    1. 短周期均线 (Short MA) 上穿 长周期均线 (Long MA) -> 买入 (Golden Cross)
    2. 短周期均线 (Short MA) 下穿 长周期均线 (Long MA) -> 卖出 (Death Cross)
    """

    def on_init(self, context: Context):
        self.symbol = "BTC/USDT"
        self.quantity = 0.01
        
        # 均线参数
        self.short_window = 5
        self.long_window = 10
        
        # 策略状态
        self.current_pos = 0.0 # 当前持仓数量
        
        print(f"DualMAStrategy Initialized: {self.symbol}, Qty={self.quantity}, "
              f"Windows={self.short_window}/{self.long_window}")

    def on_start(self, context: Context):
        print("DualMAStrategy Started")

    def on_timer(self, context: Context):
        """
        定时触发逻辑 (例如每分钟触发一次)
        """
        try:
            # 1. 获取历史K线数据
            # 需要足够的长度来计算长周期均线 (至少 long_window + 1 个点用于判断交叉)
            limit = self.long_window + 5
            df = self.sdk.get_history_kline(self.symbol, limit=limit)
            
            if df is None or len(df) < limit:
                print("Insufficient data")
                return

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
            
            if golden_cross:
                print(f"Signal: Golden Cross detected at {curr['close']}")
                # 如果当前没有持仓，则买入
                if self.current_pos <= 0:
                    print(f"Action: Buying {self.quantity} {self.symbol}")
                    self.buy(context, self.symbol, float(curr['close']), self.quantity, OrderType.MARKET_ORDER_TYPE)
            
            elif death_cross:
                print(f"Signal: Death Cross detected at {curr['close']}")
                # 如果当前持有仓位，则卖出
                if self.current_pos >= 0:
                    print(f"Action: Selling {self.quantity} {self.symbol}")
                    self.sell(context, self.symbol, float(curr['close']), self.quantity, OrderType.MARKET_ORDER_TYPE)

        except Exception as e:
            print(f"Error in on_timer: {e}")

    def on_order_status(self, context: Context, order: Order):
        """
        订单状态更新回调
        """
        print(f"Order Update: ID={order.order_id}, Status={order.status}, Filled={order.executed_size}")
        
        # 简单维护持仓状态
        if order.status == OrderStatusType.FILLED_ORDER_STATUS_TYPE:
            filled_qty = float(order.executed_size)
            if order.direction_type.name == 'BUY_DIRECTION_TYPE':
                self.current_pos += filled_qty
            elif order.direction_type.name == 'SELL_DIRECTION_TYPE':
                self.current_pos -= filled_qty
            
            print(f"Current Position: {self.current_pos}")
