/**
 * K 线图表组件
 * 
 * 使用 TradingView Lightweight Charts 实现交互式 K 线图表
 */

import { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import type { IChartApi, ISeriesApi } from 'lightweight-charts';
import type { BarData, OrderData, DecisionInfo } from '../types/data';
import { convertBarsToChartData, convertOrdersToMarkers } from '../utils/dataParser';

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

    // 创建 K 线系列
    // @ts-ignore - TradingView Charts v5 API 类型定义问题
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    seriesRef.current = candlestickSeries as any;

    // 转换并设置数据
    const chartData = convertBarsToChartData(bars);
    candlestickSeries.setData(chartData as any);

    // 添加技术指标线（从决策信息中提取）
    if (decisions && decisions.length > 0) {
      const indicators = new Set<string>();
      decisions.forEach(decision => {
        Object.keys(decision.indicators).forEach(key => indicators.add(key));
      });

      // 绘制 MA5 和 MA20（如果存在）
      if (indicators.has('MA5') && bars.length >= 5) {
        const ma5Data = calculateMA(bars, 5);
        // @ts-ignore - TradingView Charts v5 API 类型定义问题
        const ma5Series = chart.addLineSeries({
          color: '#2196F3',
          lineWidth: 2,
          title: 'MA5',
        });
        ma5Series.setData(ma5Data as any);
      }

      if (indicators.has('MA20') && bars.length >= 20) {
        const ma20Data = calculateMA(bars, 20);
        // @ts-ignore - TradingView Charts v5 API 类型定义问题
        const ma20Series = chart.addLineSeries({
          color: '#FF9800',
          lineWidth: 2,
          title: 'MA20',
        });
        ma20Series.setData(ma20Data as any);
      }
    }

    // 添加订单标记
    if (orders && orders.length > 0) {
      const markers = convertOrdersToMarkers(orders);
      (candlestickSeries as any).setMarkers(markers);
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

