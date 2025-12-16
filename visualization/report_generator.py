"""
报告生成模块

负责生成完整的HTML可视化报告。
"""

from typing import Optional
from datetime import datetime
from pathlib import Path

from .data_collector import VisualizationDataCollector
from .chart_generator import ChartGenerator


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, collector: VisualizationDataCollector):
        """
        初始化报告生成器
        
        Args:
            collector: 数据收集器实例
        """
        self.collector = collector
        self.chart_generator = ChartGenerator()
    
    def generate(self, output_path: str):
        """
        生成HTML报告
        
        Args:
            output_path: 输出文件路径
        """
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成K线图表
        chart_image = self.chart_generator.generate_kline_chart(
            bars=self.collector.bars,
            orders=self.collector.orders if self.collector.orders else None,
            decisions=self.collector.decisions if hasattr(self.collector, 'decisions') and self.collector.decisions else None,
            title=f"{self.collector.strategy_name} - K线图表"
        )
        
        # 生成HTML内容
        html_content = self._generate_html(chart_image)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html(self, chart_image: str) -> str:
        """生成HTML内容"""
        summary = self.collector.get_summary()
        
        # 生成交易详情表格
        trade_details_html = self._generate_trade_details_html()
        
        # 生成策略执行时间线
        timeline_html = self._generate_timeline_html()
        
        # 生成框架功能验证面板
        framework_html = self._generate_framework_html()
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略测试报告 - {summary['strategy_name']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-left: 4px solid #4CAF50;
            padding-left: 10px;
        }}
        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }}
        .metadata-item {{
            display: flex;
            flex-direction: column;
        }}
        .metadata-label {{
            font-size: 12px;
            color: #888;
            margin-bottom: 5px;
        }}
        .metadata-value {{
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .buy {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .sell {{
            color: #f44336;
            font-weight: bold;
        }}
        .status-success {{
            color: #4CAF50;
        }}
        .status-failure {{
            color: #f44336;
        }}
        .timeline {{
            margin: 20px 0;
        }}
        .timeline-item {{
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #4CAF50;
            background-color: #f9f9f9;
        }}
        .framework-check {{
            display: flex;
            align-items: center;
            padding: 8px;
            margin: 5px 0;
        }}
        .framework-check.success {{
            color: #4CAF50;
        }}
        .framework-check.failure {{
            color: #f44336;
        }}
        .statistics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>策略测试报告</h1>
        
        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">策略名称</span>
                <span class="metadata-value">{summary['strategy_name']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">交易品种</span>
                <span class="metadata-value">{summary['symbol']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">市场类型</span>
                <span class="metadata-value">{summary['market_type']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">测试开始时间</span>
                <span class="metadata-value">{summary['test_start_time'] or 'N/A'}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">测试结束时间</span>
                <span class="metadata-value">{summary['test_end_time'] or 'N/A'}</span>
            </div>
        </div>
        
        <h2>K线图表</h2>
        <div class="chart-container">
            {f'<img src="data:image/png;base64,{chart_image}" alt="K线图表">' if chart_image else '<p>暂无K线数据</p>'}
        </div>
        
        <h2>交易统计</h2>
        <div class="statistics">
            <div class="stat-card">
                <div class="stat-value">{summary['total_orders']}</div>
                <div class="stat-label">总交易次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['buy_orders']}</div>
                <div class="stat-label">买入次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['sell_orders']}</div>
                <div class="stat-label">卖出次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['average_price']:.2f}</div>
                <div class="stat-label">平均价格</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['total_trade_amount']:.2f}</div>
                <div class="stat-label">总交易金额</div>
            </div>
        </div>
        
        {trade_details_html}
        {timeline_html}
        {framework_html}
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #888; font-size: 12px;">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>WealthAI 策略测试框架</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_trade_details_html(self) -> str:
        """生成交易详情表格HTML"""
        if not self.collector.orders:
            return "<h2>交易详情</h2><p>暂无交易记录</p>"
        
        rows = []
        for order in self.collector.orders:
            direction_class = "buy" if order.direction == "buy" else "sell"
            direction_text = "买入" if order.direction == "buy" else "卖出"
            time_str = datetime.fromtimestamp(order.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            rows.append(f"""
                <tr>
                    <td>{time_str}</td>
                    <td class="{direction_class}">{direction_text}</td>
                    <td>{order.symbol}</td>
                    <td>{order.price:.4f}</td>
                    <td>{order.quantity:.4f}</td>
                    <td>{order.order_type}</td>
                    <td>{order.status}</td>
                    <td>{order.trigger_reason or 'N/A'}</td>
                </tr>
            """)
        
        return f"""
        <h2>交易详情</h2>
        <table>
            <thead>
                <tr>
                    <th>交易时间</th>
                    <th>方向</th>
                    <th>品种</th>
                    <th>价格</th>
                    <th>数量</th>
                    <th>订单类型</th>
                    <th>状态</th>
                    <th>触发原因</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _generate_timeline_html(self) -> str:
        """生成策略执行时间线HTML"""
        if not self.collector.function_calls:
            return "<h2>策略执行时间线</h2><p>暂无函数调用记录</p>"
        
        items = []
        for call in self.collector.function_calls:
            time_str = datetime.fromtimestamp(call.timestamp / 1000).strftime('%H:%M:%S.%f')[:-3]
            status_class = "status-success" if call.result == "success" else "status-failure"
            status_text = "✓ 成功" if call.result == "success" else "✗ 失败"
            
            items.append(f"""
                <div class="timeline-item">
                    <strong>{call.function_name}</strong>
                    <span class="{status_class}" style="float: right;">{status_text}</span>
                    <div style="font-size: 12px; color: #888;">{time_str}</div>
                    {f'<div style="font-size: 12px; color: #f44336;">{call.error_message}</div>' if call.error_message else ''}
                </div>
            """)
        
        return f"""
        <h2>策略执行时间线</h2>
        <div class="timeline">
            {''.join(items)}
        </div>
        """
    
    def _generate_framework_html(self) -> str:
        """生成框架功能验证面板HTML"""
        if not self.collector.framework_checks:
            return "<h2>框架功能验证</h2><p>暂无验证数据</p>"
        
        items = []
        for check in self.collector.framework_checks:
            status_class = "success" if check.status else "failure"
            status_icon = "✓" if check.status else "✗"
            
            items.append(f"""
                <div class="framework-check {status_class}">
                    <span style="margin-right: 10px; font-size: 18px;">{status_icon}</span>
                    <span><strong>{check.feature_name}</strong></span>
                    {f'<span style="margin-left: 10px; font-size: 12px; color: #888;">{check.details}</span>' if check.details else ''}
                </div>
            """)
        
        return f"""
        <h2>框架功能验证</h2>
        <div>
            {''.join(items)}
        </div>
        """

