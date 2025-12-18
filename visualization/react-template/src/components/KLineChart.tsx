/**
 * K 线图表组件
 * 
 * 使用 TradingView Lightweight Charts 实现交互式 K 线图表
 */

import { useEffect, useRef } from 'react';
import { 
  createChart, 
  ColorType,
  type IChartApi, 
  type ISeriesApi,
  CandlestickSeries,
  LineSeries
} from 'lightweight-charts';
import type { BarData, OrderData, DecisionInfo } from '../types/data';
import { convertBarsToChartData } from '../utils/dataParser';

interface KLineChartProps {
  bars: BarData[];
  orders?: OrderData[];
  decisions?: DecisionInfo[];
  height?: number;
}

export function KLineChart({ bars, orders, decisions, height = 400 }: KLineChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 创建图表
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1, // 十字线模式
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // 创建 K 线系列（v5 API: 使用 addSeries 方法）
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    seriesRef.current = candlestickSeries;

    // 转换并设置数据
    const chartData = convertBarsToChartData(bars);
    // 确保时间类型正确（TradingView v5 需要 Time 类型）
    const chartDataWithTime = chartData.map(item => ({
      ...item,
      time: item.time as any, // 转换为 TradingView 的 Time 类型
    }));
    candlestickSeries.setData(chartDataWithTime);

    // 添加技术指标线（从bars的indicators字段或决策信息中提取）
    const indicators = new Set<string>();
    
    // 首先从bars中提取指标（优先使用）
    bars.forEach(bar => {
      if (bar.indicators) {
        Object.keys(bar.indicators).forEach(key => indicators.add(key));
      }
    });
    
    // 如果没有从bars中获取到指标，尝试从决策信息中提取
    if (indicators.size === 0 && decisions && decisions.length > 0) {
      decisions.forEach(decision => {
        Object.keys(decision.indicators).forEach(key => indicators.add(key));
      });
    }

    // 绘制所有可用的技术指标
    // 只要有bars数据，就尝试绘制指标（优先使用bars中的indicators，如果没有则计算）
    if (bars.length > 0) {
      // MA5 - 优先使用bars中的indicators数据
      if (bars.some(b => b.indicators?.MA5)) {
        const ma5Data = bars
          .filter(b => b.indicators?.MA5)
          .map(b => ({
            time: (b.open_time / 1000) as any,
            value: parseFloat(b.indicators!.MA5),
          }));
        if (ma5Data.length > 0) {
          const ma5Series = chart.addSeries(LineSeries, {
            color: '#2196F3',
            lineWidth: 2,
            title: 'MA5',
          });
          ma5Series.setData(ma5Data);
        }
      } else if (bars.length >= 5) {
        // 如果没有指标数据，计算MA5
        const ma5Data = calculateMA(bars, 5);
        const ma5Series = chart.addSeries(LineSeries, {
          color: '#2196F3',
          lineWidth: 2,
          title: 'MA5',
        });
        ma5Series.setData(ma5Data);
      }

      // MA10
      if (bars.some(b => b.indicators?.MA10)) {
        const ma10Data = bars
          .filter(b => b.indicators?.MA10)
          .map(b => ({
            time: (b.open_time / 1000) as any,
            value: parseFloat(b.indicators!.MA10),
          }));
        if (ma10Data.length > 0) {
          const ma10Series = chart.addSeries(LineSeries, {
            color: '#00BCD4',
            lineWidth: 2,
            title: 'MA10',
          });
          ma10Series.setData(ma10Data);
        }
      }

      // MA20 - 优先使用bars中的indicators数据
      if (bars.some(b => b.indicators?.MA20)) {
        const ma20Data = bars
          .filter(b => b.indicators?.MA20)
          .map(b => ({
            time: (b.open_time / 1000) as any,
            value: parseFloat(b.indicators!.MA20),
          }));
        if (ma20Data.length > 0) {
          const ma20Series = chart.addSeries(LineSeries, {
            color: '#FF9800',
            lineWidth: 2,
            title: 'MA20',
          });
          ma20Series.setData(ma20Data);
        }
      } else if (bars.length >= 20) {
        // 如果没有指标数据，计算MA20
        const ma20Data = calculateMA(bars, 20);
        const ma20Series = chart.addSeries(LineSeries, {
          color: '#FF9800',
          lineWidth: 2,
          title: 'MA20',
        });
        ma20Series.setData(ma20Data);
      }

      // MA30
      if (bars.some(b => b.indicators?.MA30)) {
        const ma30Data = bars
          .filter(b => b.indicators?.MA30)
          .map(b => ({
            time: (b.open_time / 1000) as any,
            value: parseFloat(b.indicators!.MA30),
          }));
        if (ma30Data.length > 0) {
          const ma30Series = chart.addSeries(LineSeries, {
            color: '#9C27B0',
            lineWidth: 2,
            title: 'MA30',
          });
          ma30Series.setData(ma30Data);
        }
      }

      // 布林带
      if (bars.some(b => b.indicators?.BB_Upper && b.indicators?.BB_Lower)) {
        const bbUpperData = bars
          .filter(b => b.indicators?.BB_Upper)
          .map(b => ({
            time: (b.open_time / 1000) as any,
            value: parseFloat(b.indicators!.BB_Upper),
          }));
        const bbLowerData = bars
          .filter(b => b.indicators?.BB_Lower)
          .map(b => ({
            time: (b.open_time / 1000) as any,
            value: parseFloat(b.indicators!.BB_Lower),
          }));
        const bbMiddleData = bars
          .filter(b => b.indicators?.BB_Middle)
          .map(b => ({
            time: (b.open_time / 1000) as any,
            value: parseFloat(b.indicators!.BB_Middle),
          }));
        
        if (bbUpperData.length > 0) {
          const bbUpperSeries = chart.addSeries(LineSeries, {
            color: '#F44336',
            lineWidth: 1,
            lineStyle: 2, // dashed
            title: 'BB上轨',
          });
          bbUpperSeries.setData(bbUpperData);
          
          const bbLowerSeries = chart.addSeries(LineSeries, {
            color: '#4CAF50',
            lineWidth: 1,
            lineStyle: 2, // dashed
            title: 'BB下轨',
          });
          bbLowerSeries.setData(bbLowerData);
          
          const bbMiddleSeries = chart.addSeries(LineSeries, {
            color: '#FF9800',
            lineWidth: 1,
            lineStyle: 1, // dotted
            title: 'BB中轨',
          });
          bbMiddleSeries.setData(bbMiddleData);
        }
      }
    }

    // 添加订单标记（买卖点）
    if (orders && orders.length > 0) {
      // 为每个订单创建标记点（使用 LineSeries 绘制）
      orders.forEach(order => {
        const isBuy = order.direction === 'buy';
        const price = parseFloat(order.price);
        
        // 找到最接近订单时间的K线（允许在前后5分钟内匹配）
        let closestBar = bars[0];
        let minTimeDiff = Math.abs(bars[0].open_time - order.timestamp);
        const maxTimeDiff = 5 * 60 * 1000; // 5分钟
        
        for (const bar of bars) {
          const timeDiff = Math.abs(bar.open_time - order.timestamp);
          if (timeDiff < minTimeDiff && timeDiff <= maxTimeDiff) {
            minTimeDiff = timeDiff;
            closestBar = bar;
          }
        }
        
        // 创建标记点系列（使用散点图效果）
        const markerSeries = chart.addSeries(LineSeries, {
          color: isBuy ? '#26a69a' : '#ef5350',
          lineWidth: 1,
          pointMarkersVisible: true,
          pointMarkersRadius: 8,
          title: `${isBuy ? '买入' : '卖出'} ${order.quantity}@${price.toFixed(2)}`,
        });
        
        // 设置标记点数据（在订单位置绘制一个点）
        markerSeries.setData([{
          time: (closestBar.open_time / 1000) as any,
          value: price,
        }]);
      });
      
      console.log(`✅ 已添加 ${orders.length} 个买卖点标记到K线图`);
    }

    // 自适应大小
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // 清理
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [bars, orders, decisions, height]);

  return (
    <div style={{ width: '100%', height: `${height}px` }} ref={chartContainerRef} />
  );
}

/**
 * 计算移动平均线
 */
function calculateMA(bars: BarData[], period: number) {
  const result: Array<{ time: any; value: number }> = [];
  
  for (let i = period - 1; i < bars.length; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) {
      sum += parseFloat(bars[j].close);
    }
    const ma = sum / period;
    result.push({
      time: (bars[i].open_time / 1000) as any,
      value: ma,
    });
  }
  
  return result;
}

