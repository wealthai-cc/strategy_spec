# Design: 策略测试可视化前端

## Context

当前策略测试工具（`test_strategy.py`）通过命令行输出测试结果，但无法直观地：
- 查看K线数据和价格走势
- 看到策略的买卖点标记
- 理解策略执行的时间线和逻辑
- 判断策略是否合理执行
- 验证框架功能是否生效

需要创建一个可视化前端来帮助开发者理解策略执行过程和框架行为。

## Goals / Non-Goals

### Goals
1. **K线图表展示**: 清晰展示测试数据的K线走势
2. **买卖点标记**: 在K线图上标记策略的买入/卖出信号
3. **交易详情**: 显示每个交易点的完整信息（价格、数量、时间、原因）
4. **策略执行时间线**: 展示策略函数的调用顺序和时间
5. **框架功能验证**: 展示框架功能是否正常（函数注入、API调用）
6. **HTML 报告**: 生成可分享的 HTML 报告

### Non-Goals
- 实时策略监控（仅用于测试可视化）
- 复杂的回测分析（仅展示单次测试结果）
- 多策略对比（单策略可视化）
- 交互式回测（仅静态报告）

## Decisions

### Decision 1: 图表库选择

**What**: 使用 matplotlib 作为主要图表库

**Why**:
- 轻量级，无需浏览器环境
- 支持静态图片生成（可嵌入 HTML）
- Python 生态成熟，文档完善
- 支持 candlestick 图表（K线图）

**Alternatives considered**:
- **plotly**: 交互式图表，但需要浏览器环境，增加复杂度
- **bokeh**: 类似 plotly，但学习曲线较陡

**Implementation**:
```python
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates

# 生成K线图
fig, ax = plt.subplots(figsize=(12, 6))
# 绘制K线
# 标记买卖点
```

### Decision 2: 数据收集方式

**What**: 在 `test_strategy.py` 执行过程中收集数据

**Why**:
- 不修改引擎核心代码，保持解耦
- 测试工具层收集数据，不影响策略执行
- 可以收集完整的执行上下文

**Implementation**:
```python
class VisualizationDataCollector:
    def __init__(self):
        self.bars = []
        self.orders = []
        self.function_calls = []
        self.framework_checks = []
    
    def collect_bar(self, bar_data):
        """收集K线数据"""
        pass
    
    def collect_order(self, order_op):
        """收集订单操作"""
        pass
    
    def collect_function_call(self, func_name, timestamp, result):
        """收集函数调用"""
        pass
```

### Decision 3: 买卖点标记策略

**What**: 在K线图上使用箭头和标签标记买卖点

**Why**:
- 箭头清晰表示方向（向上=买入，向下=卖出）
- 标签显示关键信息（价格、数量）
- 颜色区分（绿色=买入，红色=卖出）

**Implementation**:
```python
# 买入点：绿色向上箭头
ax.annotate('买入', xy=(buy_time, buy_price), 
            arrowprops=dict(arrowstyle='^', color='green', lw=2))

# 卖出点：红色向下箭头
ax.annotate('卖出', xy=(sell_time, sell_price), 
            arrowprops=dict(arrowstyle='v', color='red', lw=2))
```

### Decision 4: HTML 报告结构

**What**: 使用单页 HTML 报告，包含多个面板

**Why**:
- 单页报告易于分享和查看
- 可以嵌入图表（base64 图片）
- 支持打印和导出

**Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>策略测试报告</title>
    <style>...</style>
</head>
<body>
    <h1>策略测试报告</h1>
    <section id="kline-chart">
        <!-- K线图表（base64 图片） -->
    </section>
    <section id="trade-details">
        <!-- 交易详情表格 -->
    </section>
    <section id="execution-timeline">
        <!-- 策略执行时间线 -->
    </section>
    <section id="framework-verification">
        <!-- 框架功能验证 -->
    </section>
</body>
</html>
```

### Decision 5: 集成方式

**What**: 通过命令行参数启用可视化，保持向后兼容

**Why**:
- 不破坏现有工作流
- 用户可以选择是否生成可视化
- 可以逐步推广使用

**Implementation**:
```python
# test_strategy.py
def test_strategy(strategy_path: str, visualize: bool = False, output_path: str = None):
    # ... 执行策略测试 ...
    
    if visualize:
        from visualization.report_generator import generate_report
        report_path = output_path or f"strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        generate_report(collector, report_path)
        print(f"可视化报告已生成: {report_path}")

# 命令行使用
# python3 test_strategy.py strategy/double_mean.py --visualize
# python3 test_strategy.py strategy/double_mean.py --visualize --output report.html
```

## Risks / Trade-offs

### Risk 1: 性能影响
**Risk**: 生成图表和报告可能影响测试速度

**Mitigation**: 
- 图表生成异步进行
- 提供选项禁用可视化
- 优化图表生成算法

### Risk 2: 依赖管理
**Risk**: 添加 matplotlib 依赖可能增加项目复杂度

**Mitigation**:
- matplotlib 是成熟稳定的库
- 可以标记为可选依赖
- 提供清晰的安装说明

### Risk 3: 数据收集完整性
**Risk**: 可能遗漏某些重要的执行信息

**Mitigation**:
- 在测试工具中全面收集数据
- 提供扩展接口供未来添加更多信息
- 用户反馈驱动改进

## Migration Plan

### Phase 1: 基础实现
1. 实现数据收集模块
2. 实现基础K线图表
3. 实现买卖点标记
4. 生成简单的 HTML 报告

### Phase 2: 完善功能
1. 添加交易详情面板
2. 添加策略执行时间线
3. 添加框架功能验证面板
4. 优化报告样式

### Phase 3: 集成和优化
1. 集成到 `test_strategy.py`
2. 添加命令行参数
3. 编写文档和示例
4. 性能优化

## Open Questions

1. **图表交互性**: 是否需要交互式图表（如 plotly）？还是静态图表足够？
   - **建议**: 先实现静态图表，后续根据需求添加交互式

2. **报告格式**: 是否需要支持其他格式（PDF、PNG）？
   - **建议**: 先实现 HTML，后续根据需求添加

3. **数据导出**: 是否需要支持导出原始数据（JSON、CSV）？
   - **建议**: 后续根据需求添加

4. **多策略对比**: 是否需要支持多个策略的对比可视化？
   - **建议**: 不在当前范围，后续单独提案

