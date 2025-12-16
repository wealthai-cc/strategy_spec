"""
策略测试可视化模块

提供策略测试结果的可视化功能，包括：
- K线图表展示
- 买卖点标记
- 交易详情展示
- 策略执行时间线
- 框架功能验证
- HTML 报告生成
"""

from .data_collector import VisualizationDataCollector
from .chart_generator import ChartGenerator
from .report_generator import ReportGenerator

__all__ = [
    'VisualizationDataCollector',
    'ChartGenerator',
    'ReportGenerator',
]

