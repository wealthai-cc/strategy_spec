"""
图表生成模块

负责生成K线图表和买卖点标记。
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Optional
import base64
from io import BytesIO

from .data_collector import BarData, OrderData, DecisionInfo


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
        if bars:
            closes = [bar.close for bar in bars]
            dates = [datetime.fromtimestamp(bar.open_time / 1000) for bar in bars]
            
            # 从决策信息中提取使用的技术指标
            indicators_to_plot = set()
            if decisions:
                for decision in decisions:
                    indicators_to_plot.update(decision.indicators.keys())
            
            # 绘制MA线（如果策略使用了）
            if 'MA5' in indicators_to_plot or len(bars) >= 5:
                ma5_values = self._calculate_ma(closes, 5)
                ax.plot(dates, ma5_values, label='MA5', color='blue', linewidth=1.5, alpha=0.7)
            
            if 'MA20' in indicators_to_plot or len(bars) >= 20:
                ma20_values = self._calculate_ma(closes, 20)
                ax.plot(dates, ma20_values, label='MA20', color='orange', linewidth=1.5, alpha=0.7)
            
            # 添加图例
            if indicators_to_plot or len(bars) >= 5:
                ax.legend(loc='upper left', fontsize=8)
        
        # 标记买卖点
        if orders:
            buy_orders = [o for o in orders if o.direction == "buy"]
            sell_orders = [o for o in orders if o.direction == "sell"]
            
            # 标记买入点
            for order in buy_orders:
                order_time = datetime.fromtimestamp(order.timestamp / 1000)
                # 找到对应的K线
                for i, bar in enumerate(bars):
                    bar_time = datetime.fromtimestamp(bar.open_time / 1000)
                    if bar_time <= order_time < datetime.fromtimestamp(bar.close_time / 1000):
                        # 查找对应的决策信息
                        decision_info = None
                        if decisions:
                            for decision in decisions:
                                if (decision.symbol == order.symbol and 
                                    decision.decision_type == 'buy' and
                                    abs(decision.timestamp - order.timestamp) < 60000):  # 1分钟内
                                    decision_info = decision
                                    break
                        
                        # 构建标注文本
                        if decision_info and decision_info.indicators:
                            # 显示完整决策信息
                            indicator_text = '\n'.join([f'{k}: {v:.2f}' for k, v in decision_info.indicators.items()])
                            annotation_text = f'BUY\nPrice: {order.price:.2f}\nQty: {order.quantity:.4f}\n---\n{indicator_text}'
                            if decision_info.trigger_condition:
                                annotation_text += f'\n---\nCondition: {decision_info.trigger_condition}'
                            if decision_info.decision_reason:
                                annotation_text += f'\nReason: {decision_info.decision_reason[:30]}...'
                        else:
                            # 简化信息
                            annotation_text = f'BUY\n{order.price:.2f}\n{order.quantity:.4f}'
                        
                        # 在K线下方标记买入点（使用英文避免字体问题）
                        ax.annotate(
                            annotation_text,
                            xy=(mdates.date2num(order_time), order.price),
                            xytext=(mdates.date2num(order_time), order.price * 0.90),
                            arrowprops=dict(arrowstyle='->', color='green', lw=2, connectionstyle='arc3,rad=0'),
                            fontsize=7,
                            ha='left',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.9)
                        )
                        # 添加向上箭头标记
                        ax.plot(mdates.date2num(order_time), order.price * 0.90, '^', color='green', markersize=10)
                        break
            
            # 标记卖出点
            for order in sell_orders:
                order_time = datetime.fromtimestamp(order.timestamp / 1000)
                # 找到对应的K线
                for i, bar in enumerate(bars):
                    bar_time = datetime.fromtimestamp(bar.open_time / 1000)
                    if bar_time <= order_time < datetime.fromtimestamp(bar.close_time / 1000):
                        # 查找对应的决策信息
                        decision_info = None
                        if decisions:
                            for decision in decisions:
                                if (decision.symbol == order.symbol and 
                                    decision.decision_type == 'sell' and
                                    abs(decision.timestamp - order.timestamp) < 60000):  # 1分钟内
                                    decision_info = decision
                                    break
                        
                        # 构建标注文本
                        if decision_info and decision_info.indicators:
                            # 显示完整决策信息
                            indicator_text = '\n'.join([f'{k}: {v:.2f}' for k, v in decision_info.indicators.items()])
                            annotation_text = f'SELL\nPrice: {order.price:.2f}\nQty: {order.quantity:.4f}\n---\n{indicator_text}'
                            if decision_info.trigger_condition:
                                annotation_text += f'\n---\nCondition: {decision_info.trigger_condition}'
                            if decision_info.decision_reason:
                                annotation_text += f'\nReason: {decision_info.decision_reason[:30]}...'
                        else:
                            # 简化信息
                            annotation_text = f'SELL\n{order.price:.2f}\n{order.quantity:.4f}'
                        
                        # 在K线上方标记卖出点（使用英文避免字体问题）
                        ax.annotate(
                            annotation_text,
                            xy=(mdates.date2num(order_time), order.price),
                            xytext=(mdates.date2num(order_time), order.price * 1.10),
                            arrowprops=dict(arrowstyle='->', color='red', lw=2, connectionstyle='arc3,rad=0'),
                            fontsize=7,
                            ha='left',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.9)
                        )
                        # 添加向下箭头标记
                        ax.plot(mdates.date2num(order_time), order.price * 1.10, 'v', color='red', markersize=10)
                        break
        
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
            MA值列表（前面不足period个数据的点用None填充）
        """
        ma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                ma_values.append(prices[i])  # 前面不足period个数据，使用当前价格
            else:
                ma = sum(prices[i - period + 1:i + 1]) / period
                ma_values.append(ma)
        return ma_values

