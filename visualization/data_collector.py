"""
数据收集模块

负责在策略测试执行过程中收集可视化所需的数据：
- K线数据
- 订单操作
- 函数调用记录
- 框架功能验证结果
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class BarData:
    """K线数据"""
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str


@dataclass
class OrderData:
    """订单数据"""
    order_id: Optional[str]
    symbol: str
    direction: str  # 'buy' or 'sell'
    price: float
    quantity: float
    timestamp: int
    order_type: str  # 'market', 'limit', etc.
    status: str
    trigger_reason: Optional[str] = None  # 策略逻辑触发条件
    bar_index: Optional[int] = None  # K线索引（用于回测场景，直接定位到对应的K线）


@dataclass
class FunctionCall:
    """函数调用记录"""
    function_name: str
    timestamp: int
    result: str  # 'success', 'failure', 'error'
    error_message: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None


@dataclass
class FrameworkCheck:
    """框架功能验证"""
    feature_name: str
    status: bool  # True = 正常, False = 异常
    details: Optional[str] = None


@dataclass
class DecisionInfo:
    """策略决策信息"""
    timestamp: int
    symbol: str
    decision_type: str  # 'buy', 'sell', 'hold'
    indicators: Dict[str, float]  # 技术指标值，如 {'MA5': 10.65, 'MA20': 10.50}
    trigger_condition: Optional[str] = None  # 触发条件，如 "price > MA5 * 1.01"
    condition_result: Optional[bool] = None  # 条件判断结果
    decision_reason: Optional[str] = None  # 决策依据，如 "价格高于均价1%，买入"
    strategy_state: Optional[Dict[str, Any]] = None  # 策略状态，如可用资金、持仓等


class VisualizationDataCollector:
    """
    可视化数据收集器
    
    在策略测试执行过程中收集所有可视化所需的数据。
    """
    
    def __init__(self):
        """初始化数据收集器"""
        self.bars: List[BarData] = []
        self.orders: List[OrderData] = []
        self.function_calls: List[FunctionCall] = []
        self.framework_checks: List[FrameworkCheck] = []
        self.decisions: List[DecisionInfo] = []  # 策略决策信息
        self.strategy_name: Optional[str] = None
        self.market_type: Optional[str] = None
        self.symbol: Optional[str] = None
        self.test_start_time: Optional[datetime] = None
        self.test_end_time: Optional[datetime] = None
    
    def start_test(self, strategy_name: str, market_type: str, symbol: str):
        """开始测试，记录测试元数据"""
        self.strategy_name = strategy_name
        self.market_type = market_type
        self.symbol = symbol
        self.test_start_time = datetime.now()
    
    def end_test(self):
        """结束测试，记录结束时间"""
        self.test_end_time = datetime.now()
    
    def collect_bar(self, bar_data: Dict[str, Any], symbol: str, timeframe: str):
        """
        收集K线数据
        
        Args:
            bar_data: K线数据字典，包含 open_time, close_time, open, high, low, close, volume
            symbol: 交易品种
            timeframe: 时间周期
        """
        try:
            bar = BarData(
                open_time=int(bar_data.get("open_time", 0)),
                close_time=int(bar_data.get("close_time", 0)),
                open=float(bar_data.get("open", "0")),
                high=float(bar_data.get("high", "0")),
                low=float(bar_data.get("low", "0")),
                close=float(bar_data.get("close", "0")),
                volume=float(bar_data.get("volume", "0")),
                symbol=symbol,
                timeframe=timeframe,
            )
            self.bars.append(bar)
        except (ValueError, TypeError) as e:
            # 忽略数据格式错误，继续收集其他数据
            pass
    
    def collect_order(self, order_op: Dict[str, Any], trigger_reason: Optional[str] = None):
        """
        收集订单操作
        
        Args:
            order_op: 订单操作字典，包含 order_op_type, order 等信息
            trigger_reason: 策略逻辑触发条件（可选）
        """
        try:
            order_data = order_op.get("order", {})
            order_op_type = order_op.get("order_op_type", 0)
            
            # 确定订单方向
            direction_type = order_data.get("direction_type", 0)
            if direction_type == 1:  # BUY_DIRECTION_TYPE
                direction = "buy"
            elif direction_type == 2:  # SELL_DIRECTION_TYPE
                direction = "sell"
            else:
                direction = "unknown"
            
            # 获取价格
            limit_price = order_data.get("limit_price")
            if limit_price:
                # 处理不同类型的 limit_price
                if isinstance(limit_price, dict):
                    price = float(limit_price.get("amount", "0"))
                elif isinstance(limit_price, (int, float)):
                    price = float(limit_price)
                elif isinstance(limit_price, str):
                    try:
                        price = float(limit_price)
                    except ValueError:
                        price = 0.0
                else:
                    price = 0.0
            else:
                # 如果没有限价，尝试从其他字段获取
                price = float(order_data.get("price", "0"))
            
            # 获取数量
            quantity = float(order_data.get("qty", "0"))
            
            # 获取订单类型
            order_type_enum = order_data.get("order_type", 0)
            order_type_map = {
                1: "market",
                2: "limit",
                3: "stop_market",
                4: "stop_limit",
            }
            order_type = order_type_map.get(order_type_enum, "unknown")
            
            # 获取订单状态
            status_enum = order_data.get("status", 0)
            status_map = {
                0: "pending",
                1: "submitted",
                2: "partially_filled",
                3: "filled",
                4: "canceled",
                5: "expired",
                6: "rejected",
            }
            status = status_map.get(status_enum, "unknown")
            
            # 获取时间戳（优先使用订单数据中的时间戳，否则使用当前时间）
            timestamp = int(datetime.now().timestamp() * 1000)
            if "timestamp" in order_data:
                timestamp = int(order_data["timestamp"])
            # 如果 order_op 中有 bar_time，也尝试使用（用于回测场景）
            elif "bar_time" in order_op:
                timestamp = int(order_op["bar_time"])
            
            # 获取 bar_index（用于回测场景，直接定位到对应的K线）
            bar_index = None
            if "bar_index" in order_op:
                bar_index = int(order_op["bar_index"])
            elif "bar_index" in order_data:
                bar_index = int(order_data["bar_index"])
            
            order = OrderData(
                order_id=order_data.get("unique_id") or order_data.get("order_id"),
                symbol=order_data.get("symbol", ""),
                direction=direction,
                price=price,
                quantity=quantity,
                timestamp=timestamp,
                order_type=order_type,
                status=status,
                trigger_reason=trigger_reason,
                bar_index=bar_index,
            )
            self.orders.append(order)
        except (ValueError, TypeError, KeyError) as e:
            # 忽略数据格式错误，继续收集其他数据
            pass
    
    def collect_function_call(
        self,
        function_name: str,
        result: str = "success",
        error_message: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None
    ):
        """
        收集函数调用记录
        
        Args:
            function_name: 函数名称
            result: 执行结果 ('success', 'failure', 'error')
            error_message: 错误信息（如果有）
            arguments: 函数参数（可选）
        """
        call = FunctionCall(
            function_name=function_name,
            timestamp=int(datetime.now().timestamp() * 1000),
            result=result,
            error_message=error_message,
            arguments=arguments,
        )
        self.function_calls.append(call)
    
    def collect_framework_check(self, feature_name: str, status: bool, details: Optional[str] = None):
        """
        收集框架功能验证结果
        
        Args:
            feature_name: 功能名称
            status: 状态 (True = 正常, False = 异常)
            details: 详细信息（可选）
        """
        check = FrameworkCheck(
            feature_name=feature_name,
            status=status,
            details=details,
        )
        self.framework_checks.append(check)
    
    def collect_decision(
        self,
        symbol: str,
        decision_type: str,
        indicators: Optional[Dict[str, float]] = None,
        trigger_condition: Optional[str] = None,
        condition_result: Optional[bool] = None,
        decision_reason: Optional[str] = None,
        strategy_state: Optional[Dict[str, Any]] = None,
    ):
        """
        收集策略决策信息
        
        Args:
            symbol: 交易品种
            decision_type: 决策类型 ('buy', 'sell', 'hold')
            indicators: 技术指标值字典
            trigger_condition: 触发条件表达式
            condition_result: 条件判断结果
            decision_reason: 决策依据
            strategy_state: 策略状态
        """
        decision = DecisionInfo(
            timestamp=int(datetime.now().timestamp() * 1000),
            symbol=symbol,
            decision_type=decision_type,
            indicators=indicators or {},
            trigger_condition=trigger_condition,
            condition_result=condition_result,
            decision_reason=decision_reason,
            strategy_state=strategy_state,
        )
        self.decisions.append(decision)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要
        
        Returns:
            包含数据统计的字典
        """
        buy_orders = [o for o in self.orders if o.direction == "buy"]
        sell_orders = [o for o in self.orders if o.direction == "sell"]
        
        total_trade_amount = sum(o.price * o.quantity for o in self.orders)
        avg_price = total_trade_amount / len(self.orders) if self.orders else 0
        
        return {
            "strategy_name": self.strategy_name,
            "market_type": self.market_type,
            "symbol": self.symbol,
            "test_start_time": self.test_start_time.isoformat() if self.test_start_time else None,
            "test_end_time": self.test_end_time.isoformat() if self.test_end_time else None,
            "total_bars": len(self.bars),
            "total_orders": len(self.orders),
            "buy_orders": len(buy_orders),
            "sell_orders": len(sell_orders),
            "total_trade_amount": total_trade_amount,
            "average_price": avg_price,
            "function_calls": len(self.function_calls),
            "framework_checks": len(self.framework_checks),
        }
    
    def export_to_json(self, output_path: str) -> str:
        """
        导出数据为 JSON 格式（供 React 模板使用）
        
        Args:
            output_path: 输出文件路径
        
        Returns:
            输出文件的绝对路径
        """
        from .data_exporter import export_to_json
        return export_to_json(self, output_path)

