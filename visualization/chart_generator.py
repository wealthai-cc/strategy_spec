"""
图表生成模块

负责生成K线图表和买卖点标记。
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Optional, Dict
import base64
from io import BytesIO

from .data_collector import BarData, OrderData, DecisionInfo

# 配置中文字体支持
try:
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass  # 如果字体不可用，使用默认字体


class ChartGenerator:
    """图表生成器"""
    
    def __init__(self, figsize=(12, 6)):
        """
        初始化图表生成器
        
        Args:
            figsize: 图表尺寸 (width, height)
        """
        self.figsize = figsize
    
    def generate_kline_chart(
        self,
        bars: List[BarData],
        orders: Optional[List[OrderData]] = None,
        decisions: Optional[List[DecisionInfo]] = None,
        title: Optional[str] = None
    ) -> str:
        """
        生成K线图表（包含买卖点标记）
        
        Args:
            bars: K线数据列表
            orders: 订单数据列表（可选）
            title: 图表标题（可选）
        
        Returns:
            base64 编码的图片数据（用于嵌入HTML）
        """
        if not bars:
            return ""
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # 准备数据
        dates = [datetime.fromtimestamp(bar.open_time / 1000) for bar in bars]
        opens = [bar.open for bar in bars]
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        closes = [bar.close for bar in bars]
        volumes = [bar.volume for bar in bars]
        
        # 绘制K线
        for i, (date, open_price, high, low, close) in enumerate(zip(dates, opens, highs, lows, closes)):
            # 判断涨跌
            color = 'green' if close >= open_price else 'red'
            
            # 绘制影线
            ax.plot([date, date], [low, high], color='black', linewidth=0.5)
            
            # 绘制实体
            body_height = abs(close - open_price)
            body_bottom = min(open_price, close)
            rect = plt.Rectangle(
                (mdates.date2num(date) - 0.2, body_bottom),
                0.4,
                body_height,
                facecolor=color,
                edgecolor='black',
                linewidth=0.5
            )
            ax.add_patch(rect)
        
        # 计算并绘制技术指标线
        ma_values_dict = {}  # 存储所有MA值，用于后续归因分析
        if bars:
            closes = [bar.close for bar in bars]
            dates = [datetime.fromtimestamp(bar.open_time / 1000) for bar in bars]
            
            # 从决策信息中提取使用的技术指标（支持大小写不敏感）
            indicators_to_plot = set()
            if decisions:
                for decision in decisions:
                    # 统一转换为大写，便于匹配
                    indicators_to_plot.update([k.upper() for k in decision.indicators.keys()])
            
            # 默认绘制常用均线（即使没有决策信息也绘制）
            # 绘制MA5（如果有足够的数据）
            if len(bars) >= 5:
                ma5_values = self._calculate_ma(closes, 5)
                ma_values_dict['MA5'] = ma5_values
                ma_values_dict['ma5'] = ma5_values  # 同时支持小写
                ax.plot(dates, ma5_values, label='MA5', color='blue', linewidth=1.5, alpha=0.7)
            
            # 绘制MA10（如果有足够的数据）
            if len(bars) >= 10:
                ma10_values = self._calculate_ma(closes, 10)
                ma_values_dict['MA10'] = ma10_values
                ma_values_dict['ma10'] = ma10_values
                ax.plot(dates, ma10_values, label='MA10', color='cyan', linewidth=1.5, alpha=0.7)
            
            # 绘制MA20（如果有足够的数据）
            if len(bars) >= 20:
                ma20_values = self._calculate_ma(closes, 20)
                ma_values_dict['MA20'] = ma20_values
                ma_values_dict['ma20'] = ma20_values  # 同时支持小写
                ax.plot(dates, ma20_values, label='MA20', color='orange', linewidth=1.5, alpha=0.7)
            
            # 绘制MA30（如果有足够的数据）
            if len(bars) >= 30:
                ma30_values = self._calculate_ma(closes, 30)
                ma_values_dict['MA30'] = ma30_values
                ma_values_dict['ma30'] = ma30_values
                ax.plot(dates, ma30_values, label='MA30', color='purple', linewidth=1.5, alpha=0.7)
            
            # 绘制布林带（Bollinger Bands）
            if len(bars) >= 20:  # 布林带通常使用20周期
                bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes, period=20, std_dev=2)
                # 绘制布林带（使用填充区域显示）
                ax.fill_between(dates, bb_upper, bb_lower, alpha=0.1, color='gray', label='布林带区间')
                ax.plot(dates, bb_upper, label='BB上轨', color='red', linewidth=1, alpha=0.6, linestyle='--')
                ax.plot(dates, bb_middle, label='BB中轨(MA20)', color='orange', linewidth=1, alpha=0.6, linestyle=':')
                ax.plot(dates, bb_lower, label='BB下轨', color='green', linewidth=1, alpha=0.6, linestyle='--')
            
            # 绘制价格曲线（收盘价）
            ax.plot(dates, closes, label='Price', color='black', linewidth=1.5, alpha=0.8)
            
            # 添加图例（放在右上角，避免遮挡）
            ax.legend(loc='upper left', fontsize=8, ncol=2, framealpha=0.9)
        
        # 标记买卖点
        if orders:
            buy_orders = [o for o in orders if o.direction == "buy"]
            sell_orders = [o for o in orders if o.direction == "sell"]
            
            # 标记买入点
            for order in buy_orders:
                order_time = datetime.fromtimestamp(order.timestamp / 1000)
                order_time_num = mdates.date2num(order_time)
                
                # 找到对应的K线（使用更宽松的匹配）
                matched_bar_index = None
                min_time_diff = float('inf')
                
                for i, bar in enumerate(bars):
                    bar_time = datetime.fromtimestamp(bar.open_time / 1000)
                    bar_close_time = datetime.fromtimestamp(bar.close_time / 1000)
                    
                    # 精确匹配：订单时间在K线时间范围内
                    if bar_time <= order_time < bar_close_time:
                        matched_bar_index = i
                        break
                    # 宽松匹配：找到时间最接近的K线
                    else:
                        time_diff = min(abs((order_time - bar_time).total_seconds()),
                                       abs((order_time - bar_close_time).total_seconds()))
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            matched_bar_index = i
                
                # 如果找到了匹配的K线，绘制标记
                if matched_bar_index is not None:
                    i = matched_bar_index
                    bar = bars[i]
                    
                    # 查找对应的决策信息（放宽时间匹配到5分钟）
                    decision_info = None
                    if decisions:
                            for decision in decisions:
                                if (decision.symbol == order.symbol and 
                                decision.decision_type.lower() == 'buy' and
                                abs(decision.timestamp - order.timestamp) < 300000):  # 5分钟内
                                    decision_info = decision
                                    break
                        
                    # 构建归因标注文本
                    annotation_text = self._build_decision_annotation(
                        order, decision_info, ma_values_dict, i, 'buy'
                    )
                    
                    # 计算标记位置（在K线下方）
                    marker_y = order.price * 0.85
                    if marker_y < bar.low:
                        marker_y = bar.low * 0.95
                    
                    # 在K线下方标记买入点
                        ax.annotate(
                            annotation_text,
                        xy=(order_time_num, order.price),
                        xytext=(order_time_num, marker_y),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2.5, connectionstyle='arc3,rad=0.2'),
                        fontsize=8,
                            ha='left',
                        va='top',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.95, edgecolor='green', linewidth=1.5)
                        )
                        # 添加向上箭头标记
                    ax.plot(order_time_num, marker_y, '^', color='green', markersize=12, markeredgecolor='darkgreen', markeredgewidth=1.5)
                    
                    # 绘制价格与均线的关系线（如果可用）
                    if decision_info and decision_info.indicators and i < len(bars):
                        self._draw_price_ma_relationship(ax, order_time, order.price, decision_info, ma_values_dict, i, dates, 'buy')
            
            # 标记卖出点
            for order in sell_orders:
                order_time = datetime.fromtimestamp(order.timestamp / 1000)
                order_time_num = mdates.date2num(order_time)
                
                # 找到对应的K线（使用更宽松的匹配）
                matched_bar_index = None
                min_time_diff = float('inf')
                
                for i, bar in enumerate(bars):
                    bar_time = datetime.fromtimestamp(bar.open_time / 1000)
                    bar_close_time = datetime.fromtimestamp(bar.close_time / 1000)
                    
                    # 精确匹配：订单时间在K线时间范围内
                    if bar_time <= order_time < bar_close_time:
                        matched_bar_index = i
                        break
                    # 宽松匹配：找到时间最接近的K线
                    else:
                        time_diff = min(abs((order_time - bar_time).total_seconds()),
                                       abs((order_time - bar_close_time).total_seconds()))
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            matched_bar_index = i
                
                # 如果找到了匹配的K线，绘制标记
                if matched_bar_index is not None:
                    i = matched_bar_index
                    bar = bars[i]
                    
                    # 查找对应的决策信息（放宽时间匹配到5分钟）
                    decision_info = None
                    if decisions:
                            for decision in decisions:
                                if (decision.symbol == order.symbol and 
                                decision.decision_type.lower() == 'sell' and
                                abs(decision.timestamp - order.timestamp) < 300000):  # 5分钟内
                                    decision_info = decision
                                    break
                        
                    # 构建归因标注文本
                    annotation_text = self._build_decision_annotation(
                        order, decision_info, ma_values_dict, i, 'sell'
                    )
                    
                    # 计算标记位置（在K线上方）
                    marker_y = order.price * 1.15
                    if marker_y < bar.high:
                        marker_y = bar.high * 1.05
                    
                    # 在K线上方标记卖出点
                        ax.annotate(
                            annotation_text,
                        xy=(order_time_num, order.price),
                        xytext=(order_time_num, marker_y),
                        arrowprops=dict(arrowstyle='->', color='red', lw=2.5, connectionstyle='arc3,rad=-0.2'),
                        fontsize=8,
                            ha='left',
                        va='bottom',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.95, edgecolor='red', linewidth=1.5)
                        )
                        # 添加向下箭头标记
                    ax.plot(order_time_num, marker_y, 'v', color='red', markersize=12, markeredgecolor='darkred', markeredgewidth=1.5)
                    
                    # 绘制价格与均线的关系线（如果可用）
                    if decision_info and decision_info.indicators and i < len(bars):
                        self._draw_price_ma_relationship(ax, order_time, order.price, decision_info, ma_values_dict, i, dates, 'sell')
        
        # 设置标题和标签（使用英文避免字体问题）
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Time', fontsize=10)
        ax.set_ylabel('Price', fontsize=10)
        
        # 格式化时间轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.xticks(rotation=45)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 转换为 base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def _calculate_ma(self, prices: List[float], period: int) -> List[float]:
        """
        计算移动平均线
        
        Args:
            prices: 价格列表
            period: 周期
        
        Returns:
            MA值列表（前面不足period个数据的点用当前价格填充）
        """
        ma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                ma_values.append(prices[i])  # 前面不足period个数据，使用当前价格
            else:
                ma = sum(prices[i - period + 1:i + 1]) / period
                ma_values.append(ma)
        return ma_values
    
    def _calculate_bollinger_bands(
        self, 
        prices: List[float], 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> tuple:
        """
        计算布林带（Bollinger Bands）
        
        Args:
            prices: 价格列表
            period: 周期（默认20）
            std_dev: 标准差倍数（默认2.0）
        
        Returns:
            (上轨, 中轨, 下轨) 三个列表
        """
        import statistics
        
        upper_band = []
        middle_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1:
                # 前面不足period个数据，使用当前价格作为中轨
                price = prices[i]
                middle_band.append(price)
                upper_band.append(price)
                lower_band.append(price)
            else:
                # 计算中轨（MA）
                period_prices = prices[i - period + 1:i + 1]
                ma = sum(period_prices) / period
                middle_band.append(ma)
                
                # 计算标准差
                variance = sum((p - ma) ** 2 for p in period_prices) / period
                std = variance ** 0.5
                
                # 计算上下轨
                upper_band.append(ma + std_dev * std)
                lower_band.append(ma - std_dev * std)
        
        return upper_band, middle_band, lower_band
    
    def _build_decision_annotation(
        self, 
        order: OrderData, 
        decision_info: Optional[DecisionInfo], 
        ma_values_dict: Dict[str, List[float]],
        bar_index: int,
        direction: str
    ) -> str:
        """
        构建决策归因标注文本
        
        Args:
            order: 订单数据
            decision_info: 决策信息
            ma_values_dict: MA值字典
            bar_index: K线索引
            direction: 方向 ('buy' or 'sell')
        
        Returns:
            标注文本
        """
        direction_text = "买入" if direction == 'buy' else "卖出"
        lines = [f"【{direction_text}】", f"价格: {order.price:.2f}", f"数量: {order.quantity:.4f}"]
        
        if decision_info and decision_info.indicators:
            lines.append("─" * 15)
            lines.append("技术指标:")
            
            # 显示技术指标值
            for indicator_name, indicator_value in decision_info.indicators.items():
                lines.append(f"  {indicator_name}: {indicator_value:.2f}")
                
                # 显示价格与均线的关系（支持大小写不敏感）
                indicator_key = indicator_name.upper()
                if indicator_key in ma_values_dict and bar_index < len(ma_values_dict[indicator_key]):
                    ma_value = ma_values_dict[indicator_key][bar_index]
                    price = order.price
                    if price > ma_value:
                        relation = f"价格 > {indicator_name} (+{price - ma_value:.2f})"
                    elif price < ma_value:
                        relation = f"价格 < {indicator_name} ({price - ma_value:.2f})"
                    else:
                        relation = f"价格 = {indicator_name}"
                    lines.append(f"    {relation}")
            
            # 显示触发条件
            if decision_info.trigger_condition:
                lines.append("─" * 15)
                lines.append("触发条件:")
                lines.append(f"  {decision_info.trigger_condition}")
                
                # 显示条件判断结果
                if decision_info.condition_result is not None:
                    result_text = "✓ 满足" if decision_info.condition_result else "✗ 不满足"
                    lines.append(f"  结果: {result_text}")
            
            # 显示决策依据
            if decision_info.decision_reason:
                lines.append("─" * 15)
                lines.append("决策依据:")
                reason = decision_info.decision_reason
                # 如果理由太长，截断
                if len(reason) > 50:
                    reason = reason[:47] + "..."
                lines.append(f"  {reason}")
        
        return "\n".join(lines)
    
    def _draw_price_ma_relationship(
        self,
        ax,
        order_time,
        order_price: float,
        decision_info: DecisionInfo,
        ma_values_dict: Dict[str, List[float]],
        bar_index: int,
        dates: List[datetime],
        direction: str
    ):
        """
        绘制价格与均线的关系（用虚线连接）
        
        Args:
            ax: matplotlib axes
            order_time: 订单时间
            order_price: 订单价格
            decision_info: 决策信息
            ma_values_dict: MA值字典
            bar_index: K线索引
            dates: 日期列表
            direction: 方向
        """
        if bar_index >= len(dates):
            return
        
        color = 'green' if direction == 'buy' else 'red'
        order_date_num = mdates.date2num(order_time)
        
        # 为每个使用的均线绘制关系线（支持大小写不敏感）
        for indicator_name, indicator_value in decision_info.indicators.items():
            indicator_key = indicator_name.upper()
            if indicator_key in ma_values_dict and bar_index < len(ma_values_dict[indicator_key]):
                ma_value = ma_values_dict[indicator_key][bar_index]
                ma_date_num = mdates.date2num(dates[bar_index])
                
                # 绘制从价格到均线的虚线
                ax.plot(
                    [order_date_num, ma_date_num],
                    [order_price, ma_value],
                    color=color,
                    linestyle='--',
                    linewidth=1,
                    alpha=0.4
                )
                
                # 在均线上标记点
                ax.plot(ma_date_num, ma_value, 'o', color=color, markersize=4, alpha=0.6)

