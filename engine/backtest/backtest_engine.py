"""
回测引擎

负责执行策略回测，包括：
1. 遍历每根K线执行策略
2. 模拟订单成交并更新账户状态
3. 收集订单和决策信息
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from engine.engine import StrategyExecutionEngine
from engine.context.context import Context, Bar
from engine.wealthdata.wealthdata import set_context, clear_context
import wealthdata


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, strategy_path: str):
        """
        初始化回测引擎
        
        Args:
            strategy_path: 策略文件路径
        """
        self.strategy_path = strategy_path
        self.engine = StrategyExecutionEngine(strategy_path)
        self.engine.load_strategy()
        self.strategy_module = self.engine.loader._module
        
    def run_backtest(
        self,
        bars: List[Dict[str, Any]],
        initial_cash: float,
        symbol: str,
        timeframe: str = '1d'
    ) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            bars: K线数据列表
            initial_cash: 初始资金
            symbol: 交易标的
            timeframe: 时间分辨率
            
        Returns:
            包含订单列表和回测结果的字典
        """
        # 初始化账户状态
        current_cash = initial_cash
        positions = {}  # {symbol: quantity}
        
        # 收集所有订单
        all_orders = []
        
        # 设置策略模块引用
        wealthdata._set_strategy_module(self.strategy_module)
        
        # 确保策略模块中的 log 和 g 引用正确
        if hasattr(self.strategy_module, 'log'):
            self.strategy_module.log = wealthdata.log
        if hasattr(self.strategy_module, 'g'):
            self.strategy_module.g = wealthdata.g
        
        # 更新函数全局命名空间中的引用
        import inspect
        for func_name in ['before_market_open', 'market_open', 'after_market_close']:
            if hasattr(self.strategy_module, func_name):
                func = getattr(self.strategy_module, func_name)
                func_globals = func.__globals__
                func_globals['log'] = wealthdata.log
                func_globals['g'] = wealthdata.g
                func_globals['order_value'] = wealthdata.order_value
                func_globals['order_target'] = wealthdata.order_target
                func_globals['get_bars'] = wealthdata.get_bars
                func_globals['get_price'] = wealthdata.get_price
                if func_name == 'after_market_close':
                    func_globals['get_trades'] = wealthdata.get_trades
        
        # 设置 g.security
        wealthdata.g.security = symbol
        if hasattr(self.strategy_module, 'g'):
            self.strategy_module.g.security = symbol
        
        # 构建初始执行请求
        exec_request = self._build_exec_request(bars, initial_cash, symbol, timeframe, positions)
        
        # 初始化策略
        temp_context = self.engine._build_context(exec_request)
        self.engine.lifecycle.initialize(temp_context)
        
        # 回测逻辑：遍历每根K线
        print(f"  开始回测，共 {len(bars)} 根K线...")
        
        for bar_idx, bar_data in enumerate(bars):
            # 设置当前K线
            current_bar = Bar(
                open_time=bar_data.get("open_time", 0),
                close_time=bar_data.get("close_time", 0),
                open=bar_data.get("open", "0"),
                high=bar_data.get("high", "0"),
                low=bar_data.get("low", "0"),
                close=bar_data.get("close", "0"),
                volume=bar_data.get("volume", "0"),
            )
            temp_context.current_bar = current_bar
            
            # 更新 market_data_context，只包含当前K线及之前的所有K线
            historical_bars = bars[:bar_idx + 1]
            exec_request['market_data_context'][0]['bars'] = historical_bars
            
            # 更新账户状态到 context
            self._update_context_account(temp_context, current_cash, positions, symbol)
            
            set_context(temp_context)
            
            # 调用 before_market_open
            if hasattr(self.strategy_module, 'before_market_open'):
                try:
                    before_market_open_func = getattr(self.strategy_module, 'before_market_open')
                    before_market_open_func(temp_context)
                except Exception as e:
                    pass
            
            # 调用 market_open
            if hasattr(self.strategy_module, 'market_open'):
                try:
                    market_open_func = getattr(self.strategy_module, 'market_open')
                    market_open_func(temp_context)
                    
                    # 获取生成的订单
                    order_ops = temp_context.get_order_operations()
                    
                    # 处理订单：模拟成交并更新账户状态
                    for order_op in order_ops:
                        if order_op.get("order_op_type") == 1:  # CREATE_ORDER_OP_TYPE
                            order = order_op.get("order", {})
                            order_symbol = order.get("symbol", symbol)
                            direction_type = order.get("direction_type", 0)
                            order_qty = float(order.get("qty", 0))
                            
                            # 获取订单价格
                            limit_price = order.get("limit_price")
                            if isinstance(limit_price, dict):
                                order_price = float(limit_price.get("amount", 0))
                            elif isinstance(limit_price, (int, float, str)):
                                order_price = float(limit_price)
                            else:
                                order_price = float(current_bar.close)
                            
                            # 模拟订单成交并更新账户状态
                            if direction_type == 1:  # 买入
                                if current_cash >= order_price * order_qty:
                                    current_cash -= order_price * order_qty
                                    positions[order_symbol] = positions.get(order_symbol, 0) + order_qty
                                    all_orders.append({
                                        "order_op": order_op,
                                        "bar_index": bar_idx,
                                        "bar_time": bar_data.get("open_time", 0),
                                        "executed_price": order_price,
                                        "executed_qty": order_qty,
                                    })
                            elif direction_type == 2:  # 卖出
                                current_position = positions.get(order_symbol, 0)
                                if current_position >= order_qty:
                                    current_cash += order_price * order_qty
                                    positions[order_symbol] = current_position - order_qty
                                    if positions[order_symbol] < 1e-8:
                                        del positions[order_symbol]
                                    all_orders.append({
                                        "order_op": order_op,
                                        "bar_index": bar_idx,
                                        "bar_time": bar_data.get("open_time", 0),
                                        "executed_price": order_price,
                                        "executed_qty": order_qty,
                                    })
                    
                    # 清空订单操作列表（已处理）
                    temp_context._order_operations = []
                    
                except Exception as e:
                    pass
        
        clear_context()
        
        print(f"  ✓ 回测完成，共生成 {len(all_orders)} 个订单")
        
        return {
            "orders": all_orders,
            "final_cash": current_cash,
            "final_positions": positions,
        }
    
    def _build_exec_request(
        self,
        bars: List[Dict[str, Any]],
        initial_cash: float,
        symbol: str,
        timeframe: str,
        positions: Dict[str, float]
    ) -> Dict[str, Any]:
        """构建执行请求"""
        # 确定货币类型（简化处理，假设是CNY）
        currency_type = 4  # CNY
        
        # 构建持仓列表
        positions_list = []
        for pos_symbol, qty in positions.items():
            positions_list.append({
                "symbol": pos_symbol,
                "quantity": str(qty),
                "closeable_amount": str(qty),
            })
        
        return {
            "trigger_type": 1,  # MARKET_DATA_TRIGGER_TYPE
            "trigger_detail": {},
            "market_data_context": [{
                "symbol": symbol,
                "timeframe": timeframe,
                "bars": bars,
            }],
            "account": {
                "account_id": "backtest_account",
                "account_type": 1,  # SIMULATE_ACCOUNT_TYPE
                "balances": [
                    {
                        "currency_type": currency_type,
                        "amount": initial_cash,
                    }
                ],
                "positions": positions_list,
                "total_net_value": {
                    "currency_type": currency_type,
                    "amount": initial_cash,
                },
                "available_margin": {
                    "currency_type": currency_type,
                    "amount": initial_cash,
                },
                "margin_ratio": 0.0,
                "risk_level": 0.0,
                "leverage": 1.0,
            },
            "incomplete_orders": [],
            "completed_orders": [],
            "exchange": "backtest",
            "exec_id": "backtest_exec",
            "strategy_param": {},
        }
    
    def _update_context_account(
        self,
        context: Context,
        cash: float,
        positions: Dict[str, float],
        symbol: str
    ):
        """更新 context 的账户状态"""
        # 更新可用资金
        currency_type = 4  # CNY
        context.account.available_margin = {
            "currency_type": currency_type,
            "amount": cash,
        }
        context.account.balances = [{
            "currency_type": currency_type,
            "amount": cash,
        }]
        
        # 更新持仓
        positions_list = []
        for pos_symbol, qty in positions.items():
            positions_list.append({
                "symbol": pos_symbol,
                "quantity": str(qty),
                "closeable_amount": str(qty),
            })
        context.account.positions = positions_list
        
        # 重新初始化 portfolio
        context._initialize_portfolio()

