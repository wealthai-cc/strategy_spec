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
from .data_exporter import export_to_json
from .preview_server import PreviewServer

# 可选导入（过渡期需要）
try:
    from .chart_generator import ChartGenerator
    from .report_generator import ReportGenerator
    HAS_MATPLOTLIB = True
except ImportError:
    ChartGenerator = None
    ReportGenerator = None
    HAS_MATPLOTLIB = False

__all__ = [
    'VisualizationDataCollector',
    'export_to_json',
    'PreviewServer',
    'ChartGenerator',
    'ReportGenerator',
    'HAS_MATPLOTLIB',
]

