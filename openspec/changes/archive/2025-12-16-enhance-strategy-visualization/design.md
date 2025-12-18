# Design: 增强策略测试可视化功能

## Context

当前可视化功能已经实现，但存在以下问题：
1. 需要手动启用（`--visualize` 参数）
2. 买卖点信息不足，无法判断决策是否合理
3. K线数据粒度固定为日线，不匹配策略实际使用的时间分辨率

需要改进以提供更好的策略测试和调试体验。

## Goals / Non-Goals

### Goals
1. **自动生成可视化**：每次测试自动生成报告，无需手动参数
2. **策略决策可归因**：图表展示策略决策的完整信息，包括技术指标、触发条件、决策依据
3. **时间分辨率匹配**：根据策略实际使用的时间分辨率生成测试数据
4. **增强的买卖点标记**：显示完整的决策信息，帮助理解策略逻辑

### Non-Goals
- 实时策略监控（仅用于测试可视化）
- 复杂的回测分析（仅展示单次测试结果）
- 多策略对比（单策略可视化）

## Decisions

### Decision 1: 自动生成可视化报告

**What**: 移除 `--visualize` 参数，每次测试自动生成可视化报告

**Why**:
- 可视化报告对理解策略执行非常重要，应该默认启用
- 减少用户操作步骤，提升使用体验
- 报告文件可以自动命名，不会造成混乱

**Implementation**:
```python
# test_strategy.py
def test_strategy(strategy_path: str, output_path: Optional[str] = None):
    # 总是初始化数据收集器
    collector = VisualizationDataCollector()
    
    # ... 执行测试 ...
    
    # 总是生成报告
    report_path = output_path or f"{strategy_name}_report.html"
    generator = ReportGenerator(collector)
    generator.generate(report_path)
```

### Decision 2: 时间分辨率自动检测

**What**: 从策略代码中自动检测使用的时间分辨率

**Why**:
- 策略可能使用不同的时间分辨率（1m, 5m, 1h, 1d等）
- 测试数据应该匹配策略实际使用的粒度
- 自动检测减少用户配置负担

**Implementation**:
```python
def detect_timeframe(strategy_code: str) -> str:
    """从策略代码中检测时间分辨率"""
    patterns = [
        r"get_bars\([^,]+,\s*[^,]+,\s*unit=['\"]([^'\"]+)['\"]",  # unit='1h'
        r"get_bars\([^,]+,\s*[^,]+,\s*frequency=['\"]([^'\"]+)['\"]",  # frequency='1h'
        r"get_price\([^,]+,\s*[^,]+,\s*frequency=['\"]([^'\"]+)['\"]",  # frequency='1h'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, strategy_code)
        if match:
            return match.group(1)
    
    return "1d"  # 默认日线
```

### Decision 3: 策略决策信息收集

**What**: 收集策略执行时的技术指标值、触发条件、决策依据

**Why**:
- 帮助理解策略为什么做出某个决策
- 验证策略逻辑是否正确执行
- 提供完整的决策上下文

**Implementation**:
```python
@dataclass
class DecisionInfo:
    """策略决策信息"""
    timestamp: int
    symbol: str
    decision_type: str  # 'buy', 'sell', 'hold'
    indicators: Dict[str, float]  # 技术指标值，如 {'MA5': 10.65, 'MA20': 10.50}
    trigger_condition: str  # 触发条件，如 "price > MA5 * 1.01"
    condition_result: bool  # 条件判断结果
    decision_reason: str  # 决策依据，如 "价格高于均价1%，买入"
    strategy_state: Dict[str, Any]  # 策略状态，如可用资金、持仓等
```

### Decision 4: 增强的买卖点标记

**What**: 在买卖点标记中显示完整的决策信息

**Why**:
- 当前标记只显示价格和数量，信息不足
- 需要显示技术指标、触发条件、决策依据等完整信息
- 帮助用户理解策略决策的合理性

**Implementation**:
```python
# 在图表上添加详细的标注框
annotation_text = f"""
BUY
Price: {order.price:.2f}
Qty: {order.quantity:.4f}
---
MA5: {decision_info.indicators.get('MA5', 'N/A')}
MA20: {decision_info.indicators.get('MA20', 'N/A')}
---
Condition: {decision_info.trigger_condition}
Result: {decision_info.condition_result}
---
Reason: {decision_info.decision_reason}
---
Cash: {decision_info.strategy_state.get('available_cash', 'N/A')}
"""

ax.annotate(
    annotation_text,
    xy=(order_time, order.price),
    xytext=(order_time, order.price * 0.95),
    arrowprops=dict(arrowstyle='->', color='green', lw=2),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.9),
    fontsize=8,
    ha='left',
)
```

### Decision 5: 技术指标线叠加

**What**: 在K线图上叠加技术指标线（如MA5、MA20）

**Why**:
- 帮助理解策略使用的技术指标
- 可视化指标与价格的关系
- 验证指标计算是否正确

**Implementation**:
```python
# 计算并绘制MA5线
if 'MA5' in indicators:
    ma5_values = calculate_ma(closes, 5)
    ax.plot(dates, ma5_values, label='MA5', color='blue', linewidth=1.5)

# 计算并绘制MA20线
if 'MA20' in indicators:
    ma20_values = calculate_ma(closes, 20)
    ax.plot(dates, ma20_values, label='MA20', color='orange', linewidth=1.5)

# 添加图例
ax.legend(loc='upper left')
```

## Risks / Trade-offs

### Risk 1: 时间分辨率检测不准确
**Risk**: 自动检测可能无法准确识别策略使用的时间分辨率

**Mitigation**: 
- 提供多种检测模式（正则表达式匹配）
- 如果检测失败，使用默认值并给出警告
- 允许用户手动指定时间分辨率（通过参数）

### Risk 2: 决策信息收集困难
**Risk**: 策略代码可能不直接暴露决策信息

**Mitigation**:
- 通过分析策略代码中的条件判断语句
- 通过策略执行时的日志输出
- 如果无法收集，显示占位符或提示信息

### Risk 3: 图表信息过载
**Risk**: 添加太多信息可能导致图表难以阅读

**Mitigation**:
- 使用交互式提示框（hover tooltip）显示详细信息
- 提供折叠/展开功能
- 允许用户选择显示哪些信息

## Migration Plan

### Phase 1: 自动生成和分辨率检测
1. 修改 `test_strategy.py` 移除 `--visualize` 参数
2. 实现时间分辨率自动检测
3. 根据检测结果生成对应粒度的K线数据

### Phase 2: 决策信息收集
1. 扩展 `VisualizationDataCollector` 支持决策信息收集
2. 实现策略代码分析提取决策信息
3. 实现技术指标计算和收集

### Phase 3: 图表增强
1. 在图表上叠加技术指标线
2. 增强买卖点标记显示完整信息
3. 添加图例和说明

### Phase 4: 测试和优化
1. 测试不同时间分辨率的策略
2. 测试不同决策信息的展示
3. 优化图表布局和可读性

## Open Questions

1. **决策信息收集方式**: 如何准确收集策略的决策信息？
   - **建议**: 先通过代码分析，如果失败则通过日志或占位符

2. **技术指标计算**: 是否需要在可视化模块中重新计算技术指标？
   - **建议**: 如果策略已经计算了指标，直接使用；否则在可视化模块中计算

3. **交互式图表**: 是否需要交互式图表（如 plotly）？
   - **建议**: 先实现静态图表，后续根据需求添加交互式
