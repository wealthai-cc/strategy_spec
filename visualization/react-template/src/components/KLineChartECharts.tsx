/**
 * K 线图表组件（使用 ECharts）
 * 
 * 使用 ECharts 实现交互式 K 线图表，清晰显示买卖点标记
 */

import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { BarData, OrderData, DecisionInfo } from '../types/data';
import { TradeDetailCard } from './TradeDetailCard';

interface KLineChartEChartsProps {
  bars: BarData[];
  orders?: OrderData[];
  decisions?: DecisionInfo[];
  height?: number;
  selectedOrderId?: string | null;
  selectedDecisionTimestamp?: number;
  onOrderSelect?: (orderId: string | null) => void;
  onDecisionSelect?: (timestamp: number) => void;
}

export function KLineChartECharts({ 
  bars, 
  orders, 
  decisions, 
  height = 400,
  selectedOrderId,
  selectedDecisionTimestamp,
  onOrderSelect,
  onDecisionSelect,
}: KLineChartEChartsProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  
  // 详情卡片状态
  const [detailCardVisible, setDetailCardVisible] = useState(false);
  const [detailCardPosition, setDetailCardPosition] = useState({ x: 0, y: 0 });
  const [detailCardOrder, setDetailCardOrder] = useState<OrderData | undefined>();
  const [detailCardDecision, setDetailCardDecision] = useState<DecisionInfo | undefined>();
  const [detailCardBar, setDetailCardBar] = useState<BarData | undefined>();
  
  // 聚焦模式状态
  const [focusMode, setFocusMode] = useState(false);
  const [focusedIndicators, setFocusedIndicators] = useState<string[]>([]);

  useEffect(() => {
    if (!chartContainerRef.current || bars.length === 0) {
      console.warn('KLineChartECharts: 缺少容器或数据', { 
        hasContainer: !!chartContainerRef.current, 
        barsLength: bars.length 
      });
      return;
    }

    // 初始化图表
    if (!chartRef.current) {
      chartRef.current = echarts.init(chartContainerRef.current);
    }
    const chart = chartRef.current;
    
    console.log('KLineChartECharts: 初始化图表', { 
      barsCount: bars.length, 
      ordersCount: orders?.length || 0 
    });

    // 准备K线数据（ECharts candlestick格式：[时间, 开盘, 收盘, 最低, 最高, 成交量]）
    // 注意：ECharts的category轴需要字符串，但candlestick系列需要数值数组
    const klineData = bars.map(bar => [
      parseFloat(bar.open),
      parseFloat(bar.close),
      parseFloat(bar.low),
      parseFloat(bar.high),
      parseFloat(bar.volume),
    ]);
    
    // 准备时间轴数据（字符串格式，用于category轴）
    const timeLabels = bars.map(bar => {
      const date = new Date(bar.open_time);
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    });

    // 准备技术指标数据
    const ma5Data: number[] = [];
    const ma10Data: number[] = [];
    const ma20Data: number[] = [];
    const ma30Data: number[] = [];
    const bbUpperData: number[] = [];
    const bbMiddleData: number[] = [];
    const bbLowerData: number[] = [];

    const closes = bars.map(b => parseFloat(b.close));
    
    // 计算MA
    for (let i = 0; i < bars.length; i++) {
      const bar = bars[i];
      const indicators = bar.indicators || {};
      
      if (indicators.MA5) {
        ma5Data.push(parseFloat(indicators.MA5));
      } else if (i >= 4) {
        ma5Data.push(closes.slice(i - 4, i + 1).reduce((a, b) => a + b) / 5);
      } else {
        ma5Data.push(null as any);
      }

      if (indicators.MA10) {
        ma10Data.push(parseFloat(indicators.MA10));
      } else if (i >= 9) {
        ma10Data.push(closes.slice(i - 9, i + 1).reduce((a, b) => a + b) / 10);
      } else {
        ma10Data.push(null as any);
      }

      if (indicators.MA20) {
        ma20Data.push(parseFloat(indicators.MA20));
      } else if (i >= 19) {
        ma20Data.push(closes.slice(i - 19, i + 1).reduce((a, b) => a + b) / 20);
      } else {
        ma20Data.push(null as any);
      }

      if (indicators.MA30) {
        ma30Data.push(parseFloat(indicators.MA30));
      } else if (i >= 29) {
        ma30Data.push(closes.slice(i - 29, i + 1).reduce((a, b) => a + b) / 30);
      } else {
        ma30Data.push(null as any);
      }

      // 布林带
      if (indicators.BB_Upper) {
        bbUpperData.push(parseFloat(indicators.BB_Upper));
        bbMiddleData.push(parseFloat(indicators.BB_Middle || indicators.MA20 || '0'));
        bbLowerData.push(parseFloat(indicators.BB_Lower || '0'));
      } else {
        bbUpperData.push(null as any);
        bbMiddleData.push(null as any);
        bbLowerData.push(null as any);
      }
    }

    // 准备买卖点数据（使用K线索引，而不是时间戳）
    // 同时建立订单ID到K线索引的映射，用于联动
    const buyPoints: Array<[number, number, string, string | null]> = []; // [K线索引, 价格, 标签, 订单ID]
    const sellPoints: Array<[number, number, string, string | null]> = [];
    const orderIdToBarIndex = new Map<string, number>(); // 订单ID -> K线索引

    if (orders && orders.length > 0) {
      orders.forEach(order => {
        const orderTime = order.timestamp;
        const orderPrice = parseFloat(order.price);
        const orderQty = typeof order.quantity === 'number' ? order.quantity : parseFloat(String(order.quantity));
        const orderId = order.order_id || null;
        const label = `${order.direction === 'buy' ? '买入' : '卖出'} ${orderQty}@${orderPrice.toFixed(2)}`;

        // 找到最接近的K线索引
        // 优先使用 bar_index（如果订单数据中有，用于回测场景）
        let closestBarIndex = 0;
        
        if (order.bar_index !== undefined && order.bar_index !== null) {
          // 直接使用 bar_index（回测场景）
          closestBarIndex = Math.max(0, Math.min(order.bar_index, bars.length - 1));
        } else {
          // 否则通过时间戳匹配
          let minTimeDiff = Infinity;
          let foundExactMatch = false;
          
          for (let i = 0; i < bars.length; i++) {
            const bar = bars[i];
            const barOpenTime = typeof bar.open_time === 'number' ? bar.open_time : parseInt(String(bar.open_time));
            const barCloseTime = typeof bar.close_time === 'number' ? bar.close_time : parseInt(String(bar.close_time));
            
            // 如果订单时间在K线的时间范围内，直接匹配
            if (orderTime >= barOpenTime && orderTime <= barCloseTime) {
              closestBarIndex = i;
              foundExactMatch = true;
              break;
            }
            
            // 否则计算时间差
            const timeDiff = Math.min(
              Math.abs(barOpenTime - orderTime),
              Math.abs(barCloseTime - orderTime)
            );
            if (timeDiff < minTimeDiff) {
              minTimeDiff = timeDiff;
              closestBarIndex = i;
            }
          }
          
          // 如果时间差太大（超过1天），可能是时间戳单位不匹配
          if (!foundExactMatch && minTimeDiff > 24 * 60 * 60 * 1000) {
            console.warn(`订单时间戳 ${orderTime} 与K线时间差过大 (${minTimeDiff}ms)，可能时间戳单位不匹配`);
          }
        }

        // 使用K线索引和订单价格（如果订单价格为0，使用K线的收盘价）
        const displayPrice = orderPrice > 0 ? orderPrice : parseFloat(bars[closestBarIndex]?.close || '0');
        
        // 建立订单ID到K线索引的映射
        if (orderId) {
          orderIdToBarIndex.set(orderId, closestBarIndex);
        }
        
        if (order.direction === 'buy') {
          buyPoints.push([closestBarIndex, displayPrice, label, orderId]);
        } else {
          sellPoints.push([closestBarIndex, displayPrice, label, orderId]);
        }
      });
      
      console.log('买卖点匹配结果:', {
        buyPoints: buyPoints.length,
        sellPoints: sellPoints.length,
        buyPointsSample: buyPoints.slice(0, 3),
        sellPointsSample: sellPoints.slice(0, 3),
      });
    }
    
    // 建立决策时间戳到K线索引的映射
    const decisionTimestampToBarIndex = new Map<number, number>();
    if (decisions && decisions.length > 0) {
      decisions.forEach(decision => {
        const decisionTime = decision.timestamp;
        let closestBarIndex = 0;
        let minTimeDiff = Infinity;
        
        for (let i = 0; i < bars.length; i++) {
          const bar = bars[i];
          const barOpenTime = bar.open_time;
          const barCloseTime = bar.close_time;
          
          if (decisionTime >= barOpenTime && decisionTime <= barCloseTime) {
            closestBarIndex = i;
            break;
          }
          
          const timeDiff = Math.min(
            Math.abs(barOpenTime - decisionTime),
            Math.abs(barCloseTime - decisionTime)
          );
          if (timeDiff < minTimeDiff) {
            minTimeDiff = timeDiff;
            closestBarIndex = i;
          }
        }
        decisionTimestampToBarIndex.set(decisionTime, closestBarIndex);
      });
    }
    
    // 确定当前选中的K线索引
    let selectedBarIndex: number | null = null;
    if (selectedOrderId && orderIdToBarIndex.has(selectedOrderId)) {
      selectedBarIndex = orderIdToBarIndex.get(selectedOrderId)!;
    } else if (selectedDecisionTimestamp && decisionTimestampToBarIndex.has(selectedDecisionTimestamp)) {
      selectedBarIndex = decisionTimestampToBarIndex.get(selectedDecisionTimestamp)!;
    }

    // 配置图表选项
    const option: echarts.EChartsOption = {
      title: {
        text: 'K线图',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any) => {
          if (Array.isArray(params)) {
            const dataIndex = params[0].dataIndex;
            const bar = bars[dataIndex];
            const date = bar ? new Date(bar.open_time).toLocaleString() : '';
            let result = `<div style="margin-bottom: 8px;"><strong>${date}</strong></div>`;
            params.forEach((param: any) => {
              if (param.seriesName === 'K线') {
                const data = param.data as number[];
                result += `
                  <div>开盘: ${data[0].toFixed(2)}</div>
                  <div>收盘: ${data[1].toFixed(2)}</div>
                  <div>最低: ${data[2].toFixed(2)}</div>
                  <div>最高: ${data[3].toFixed(2)}</div>
                  <div>成交量: ${data[4].toLocaleString()}</div>
                `;
              } else {
                // 处理散点图数据（买入/卖出信号），value 是数组 [index, price]
                const value = param.value;
                let displayValue = 'N/A';
                if (typeof value === 'number') {
                  displayValue = value.toFixed(2);
                } else if (Array.isArray(value) && value.length >= 2 && typeof value[1] === 'number') {
                  displayValue = value[1].toFixed(2);
                }
                result += `<div>${param.seriesName}: ${displayValue}</div>`;
              }
            });
            return result;
          }
          return '';
        },
      },
      legend: {
        data: ['K线', 'MA5', 'MA10', 'MA20', 'MA30', 'BB上轨', 'BB中轨', 'BB下轨', '买入', '卖出'],
        top: 30,
      },
      grid: [
        {
          left: '10%',
          right: '8%',
          top: '15%',
          height: '60%',
        },
        {
          left: '10%',
          right: '8%',
          top: '80%',
          height: '15%',
        },
      ],
      xAxis: [
        {
          type: 'category',
          data: timeLabels,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          axisLabel: {
            rotate: 45,
            interval: Math.floor(bars.length / 10), // 显示约10个标签
          },
        },
        {
          type: 'category',
          gridIndex: 1,
          data: timeLabels,
          boundaryGap: false,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: {
            rotate: 45,
            interval: Math.floor(bars.length / 10),
          },
        },
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          top: '95%',
          start: 50,
          end: 100,
        },
      ],
      series: [
        // K线
        {
          name: 'K线',
          type: 'candlestick',
          data: klineData,
          itemStyle: {
            color: '#ef5350', // 跌（红）
            color0: '#26a69a', // 涨（绿）
            borderColor: '#ef5350',
            borderColor0: '#26a69a',
          },
          // 高亮选中的K线
          ...(selectedBarIndex !== null ? {
            markArea: {
              silent: true,
              itemStyle: {
                color: 'rgba(255, 152, 0, 0.15)',
              },
              data: [
                [
                  { xAxis: selectedBarIndex },
                  { xAxis: selectedBarIndex }
                ]
              ] as any,
            },
          } : {}),
        },
        // MA5
        {
          name: 'MA5',
          type: 'line',
          data: focusMode && !focusedIndicators.includes('MA5') ? [] : ma5Data,
          smooth: true,
          lineStyle: {
            color: '#2196F3',
            width: 2,
          },
          symbol: 'none',
        },
        // MA10
        {
          name: 'MA10',
          type: 'line',
          data: focusMode ? [] : ma10Data,
          smooth: true,
          lineStyle: {
            color: '#00BCD4',
            width: 2,
          },
          symbol: 'none',
        },
        // MA20
        {
          name: 'MA20',
          type: 'line',
          data: focusMode ? [] : ma20Data,
          smooth: true,
          lineStyle: {
            color: '#FF9800',
            width: 2,
          },
          symbol: 'none',
        },
        // MA30
        {
          name: 'MA30',
          type: 'line',
          data: focusMode ? [] : ma30Data,
          smooth: true,
          lineStyle: {
            color: '#9C27B0',
            width: 2,
          },
          symbol: 'none',
        },
        // 布林带上轨
        {
          name: 'BB上轨',
          type: 'line',
          data: focusMode ? [] : bbUpperData,
          smooth: true,
          lineStyle: {
            color: '#F44336',
            type: 'dashed',
            width: 1,
          },
          symbol: 'none',
        },
        // 布林带中轨
        {
          name: 'BB中轨',
          type: 'line',
          data: focusMode ? [] : bbMiddleData,
          smooth: true,
          lineStyle: {
            color: '#FF9800',
            type: 'dashed',
            width: 1,
          },
          symbol: 'none',
        },
        // 布林带下轨
        {
          name: 'BB下轨',
          type: 'line',
          data: focusMode ? [] : bbLowerData,
          smooth: true,
          lineStyle: {
            color: '#4CAF50',
            type: 'dashed',
            width: 1,
          },
          symbol: 'none',
        },
        // 买入点（未选中的）
        {
          name: '买入',
          type: 'scatter',
          data: buyPoints
            .filter(([, , , orderId]) => orderId !== selectedOrderId)
            .map(([barIndex, price]) => {
              const bar = bars[barIndex];
              if (bar) {
                const lowPrice = parseFloat(bar.low);
                const displayPrice = Math.max(price, lowPrice * 0.98);
                return [barIndex, displayPrice];
              }
              return [barIndex, price];
            }),
          symbol: 'triangle',
          symbolSize: 18,
          itemStyle: {
            color: '#26a69a',
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            position: 'bottom',
            formatter: (params: any) => {
              const point = buyPoints[params.dataIndex];
              return point ? point[2] : '';
            },
            fontSize: 11,
            fontWeight: 'bold',
            color: '#26a69a',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderColor: '#26a69a',
            borderWidth: 1,
            borderRadius: 4,
            padding: [4, 6],
            shadowBlur: 4,
            shadowColor: 'rgba(0, 0, 0, 0.2)',
          },
          zlevel: 10,
        },
        // 买入点（选中的，高亮显示）
        ...(selectedOrderId && buyPoints.some(([, , , orderId]) => orderId === selectedOrderId) ? [{
          name: '买入-选中',
          type: 'scatter' as const,
          data: buyPoints
            .filter(([, , , orderId]) => orderId === selectedOrderId)
            .map(([barIndex, price]) => {
              const bar = bars[barIndex];
              if (bar) {
                const lowPrice = parseFloat(bar.low);
                const displayPrice = Math.max(price, lowPrice * 0.98);
                return [barIndex, displayPrice];
              }
              return [barIndex, price];
            }),
          symbol: 'triangle',
          symbolSize: 24,
          itemStyle: {
            color: '#00bcd4',
            borderColor: '#fff',
            borderWidth: 3,
          },
          label: {
            show: true,
            position: 'bottom' as const,
            formatter: () => {
              const point = buyPoints.find(([, , , orderId]) => orderId === selectedOrderId);
              return point ? point[2] : '';
            },
            fontSize: 12,
            fontWeight: 'bold' as const,
            color: '#00bcd4',
            backgroundColor: 'rgba(0, 188, 212, 0.2)',
            borderColor: '#00bcd4',
            borderWidth: 2,
            borderRadius: 4,
            padding: [4, 6],
          },
          zlevel: 11,
        }] : []),
        // 卖出点（未选中的）
        {
          name: '卖出',
          type: 'scatter',
          data: sellPoints
            .filter(([, , , orderId]) => orderId !== selectedOrderId)
            .map(([barIndex, price]) => {
              const bar = bars[barIndex];
              if (bar) {
                const highPrice = parseFloat(bar.high);
                const displayPrice = price > 0 ? Math.min(price, highPrice * 1.02) : highPrice * 1.02;
                return [barIndex, displayPrice];
              }
              return [barIndex, price];
            }),
          symbol: 'triangle',
          symbolRotate: 180,
          symbolSize: 18,
          itemStyle: {
            color: '#ef5350',
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            position: 'top',
            formatter: (params: any) => {
              const point = sellPoints[params.dataIndex];
              return point ? point[2] : '';
            },
            fontSize: 11,
            fontWeight: 'bold',
            color: '#ef5350',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderColor: '#ef5350',
            borderWidth: 1,
            borderRadius: 4,
            padding: [4, 6],
            shadowBlur: 4,
            shadowColor: 'rgba(0, 0, 0, 0.2)',
          },
          zlevel: 10,
        },
        // 卖出点（选中的，高亮显示）
        ...(selectedOrderId && sellPoints.some(([, , , orderId]) => orderId === selectedOrderId) ? [{
          name: '卖出-选中',
          type: 'scatter' as const,
          data: sellPoints
            .filter(([, , , orderId]) => orderId === selectedOrderId)
            .map(([barIndex, price]) => {
              const bar = bars[barIndex];
              if (bar) {
                const highPrice = parseFloat(bar.high);
                const displayPrice = price > 0 ? Math.min(price, highPrice * 1.02) : highPrice * 1.02;
                return [barIndex, displayPrice];
              }
              return [barIndex, price];
            }),
          symbol: 'triangle',
          symbolRotate: 180,
          symbolSize: 24,
          itemStyle: {
            color: '#ff5722',
            borderColor: '#fff',
            borderWidth: 3,
          },
          label: {
            show: true,
            position: 'top' as const,
            formatter: () => {
              const point = sellPoints.find(([, , , orderId]) => orderId === selectedOrderId);
              return point ? point[2] : '';
            },
            fontSize: 12,
            fontWeight: 'bold' as const,
            color: '#ff5722',
            backgroundColor: 'rgba(255, 87, 34, 0.2)',
            borderColor: '#ff5722',
            borderWidth: 2,
            borderRadius: 4,
            padding: [4, 6],
          },
          zlevel: 11,
        }] : []),
        // 成交量
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: bars.map((bar, index) => [
            index, // 使用索引而不是时间戳
            parseFloat(bar.volume),
            parseFloat(bar.close) >= parseFloat(bar.open) ? 1 : -1, // 涨跌标记
          ]),
          itemStyle: {
            color: (params: any) => {
              return params.data[2] >= 0 ? '#26a69a' : '#ef5350';
            },
          },
        },
      ],
    };

    try {
      chart.setOption(option, true); // true 表示不合并，完全替换
      console.log('KLineChartECharts: 图表配置已设置', {
        klineDataCount: klineData.length,
        buyPointsCount: buyPoints.length,
        sellPointsCount: sellPoints.length,
      });
    } catch (error) {
      console.error('KLineChartECharts: 设置图表选项失败', error);
    }

    // 点击事件处理
    const handleChartClick = (params: any) => {
      if (!chartContainerRef.current) return;

      // 检查是否点击了买卖点标记
      if (params.seriesName === '买入' || params.seriesName === '买入-选中') {
        const orderId = buyPoints[params.dataIndex]?.[3];
        if (orderId) {
          const order = orders?.find(o => o.order_id === orderId);
          const barIndex = buyPoints[params.dataIndex][0];
          const bar = bars[barIndex];
          
          // 查找对应的决策（优先匹配时间最接近的）
          let decision: DecisionInfo | undefined;
          if (decisions && decisions.length > 0) {
            // 先尝试精确匹配（在K线时间范围内）
            decision = decisions.find(d => 
              d.timestamp >= bar.open_time && d.timestamp <= bar.close_time
            );
            // 如果没有精确匹配，找时间最接近的
            if (!decision) {
              let minTimeDiff = Infinity;
              for (const d of decisions) {
                const timeDiff = Math.min(
                  Math.abs(d.timestamp - bar.open_time),
                  Math.abs(d.timestamp - bar.close_time)
                );
                if (timeDiff < minTimeDiff && timeDiff < 24 * 60 * 60 * 1000) {
                  minTimeDiff = timeDiff;
                  decision = d;
                }
              }
            }
          }

          // 计算卡片位置
          const rect = chartContainerRef.current.getBoundingClientRect();
          const x = params.offsetX + rect.left;
          const y = params.offsetY + rect.top;

          setDetailCardOrder(order);
          setDetailCardDecision(decision);
          setDetailCardBar(bar);
          setDetailCardPosition({ x, y });
          setDetailCardVisible(true);

          // 触发聚焦模式
          setFocusMode(true);
          setFocusedIndicators(['MA5']); // 买入决策基于 MA5

          // 通知父组件
          if (onOrderSelect) {
            onOrderSelect(orderId);
          }
          if (decision && onDecisionSelect) {
            onDecisionSelect(decision.timestamp);
          }
        }
      } else if (params.seriesName === '卖出' || params.seriesName === '卖出-选中') {
        const orderId = sellPoints[params.dataIndex]?.[3];
        if (orderId) {
          const order = orders?.find(o => o.order_id === orderId);
          const barIndex = sellPoints[params.dataIndex][0];
          const bar = bars[barIndex];
          
          // 查找对应的决策（优先匹配时间最接近的）
          let decision: DecisionInfo | undefined;
          if (decisions && decisions.length > 0) {
            // 先尝试精确匹配（在K线时间范围内）
            decision = decisions.find(d => 
              d.timestamp >= bar.open_time && d.timestamp <= bar.close_time
            );
            // 如果没有精确匹配，找时间最接近的
            if (!decision) {
              let minTimeDiff = Infinity;
              for (const d of decisions) {
                const timeDiff = Math.min(
                  Math.abs(d.timestamp - bar.open_time),
                  Math.abs(d.timestamp - bar.close_time)
                );
                if (timeDiff < minTimeDiff && timeDiff < 24 * 60 * 60 * 1000) {
                  minTimeDiff = timeDiff;
                  decision = d;
                }
              }
            }
          }

          // 计算卡片位置
          const rect = chartContainerRef.current.getBoundingClientRect();
          const x = params.offsetX + rect.left;
          const y = params.offsetY + rect.top;

          setDetailCardOrder(order);
          setDetailCardDecision(decision);
          setDetailCardBar(bar);
          setDetailCardPosition({ x, y });
          setDetailCardVisible(true);

          // 触发聚焦模式
          setFocusMode(true);
          setFocusedIndicators(['MA5']); // 卖出决策基于 MA5

          // 通知父组件
          if (onOrderSelect) {
            onOrderSelect(orderId);
          }
          if (decision && onDecisionSelect) {
            onDecisionSelect(decision.timestamp);
          }
        }
      }
    };

    chart.on('click', handleChartClick);

    // 键盘导航
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!detailCardVisible) return;

      if (e.key === 'Escape') {
        setDetailCardVisible(false);
        setFocusMode(false);
        setFocusedIndicators([]);
        if (onOrderSelect) onOrderSelect(null);
        if (onDecisionSelect) onDecisionSelect(0);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        // 切换买卖点（按时间顺序）
        const allTradePoints = [
          ...buyPoints.map(([barIndex, , , orderId]) => ({ barIndex, orderId, type: 'buy' as const })),
          ...sellPoints.map(([barIndex, , , orderId]) => ({ barIndex, orderId, type: 'sell' as const })),
        ].sort((a, b) => bars[a.barIndex].open_time - bars[b.barIndex].open_time);

        const currentIndex = allTradePoints.findIndex(
          p => p.orderId === detailCardOrder?.order_id
        );

        if (currentIndex >= 0) {
          const nextIndex = e.key === 'ArrowLeft' 
            ? Math.max(0, currentIndex - 1)
            : Math.min(allTradePoints.length - 1, currentIndex + 1);
          
          const nextPoint = allTradePoints[nextIndex];
          if (nextPoint) {
            const order = orders?.find(o => o.order_id === nextPoint.orderId);
            const bar = bars[nextPoint.barIndex];
            const decision = decisions?.find(d => 
              Math.abs(d.timestamp - bar.open_time) < 24 * 60 * 60 * 1000
            );

            setDetailCardOrder(order);
            setDetailCardDecision(decision);
            setDetailCardBar(bar);
            setFocusedIndicators(['MA5']);

            if (onOrderSelect) onOrderSelect(nextPoint.orderId);
            if (decision && onDecisionSelect) onDecisionSelect(decision.timestamp);

            // 自动滚动到对应位置
            if (chartRef.current) {
              const dataZoom = {
                start: Math.max(0, (nextPoint.barIndex / bars.length) * 100 - 10),
                end: Math.min(100, (nextPoint.barIndex / bars.length) * 100 + 10),
              };
              chartRef.current.dispatchAction({
                type: 'dataZoom',
                start: dataZoom.start,
                end: dataZoom.end,
              });
            }
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    // 自适应大小
    const handleResize = () => {
      if (chartRef.current) {
        chartRef.current.resize();
      }
    };

    window.addEventListener('resize', handleResize);

    // 清理
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('keydown', handleKeyDown);
      if (chartRef.current) {
        chartRef.current.off('click', handleChartClick);
        chartRef.current.dispose();
        chartRef.current = null;
      }
    };
  }, [bars, orders, decisions, height, selectedOrderId, selectedDecisionTimestamp, onOrderSelect, onDecisionSelect, detailCardVisible, detailCardOrder, focusMode, focusedIndicators]);

  // 计算卡片位置（避免超出边界）
  const calculateCardPosition = (x: number, y: number) => {
    if (!chartContainerRef.current) return { x, y };

    const rect = chartContainerRef.current.getBoundingClientRect();
    const cardWidth = 400; // 卡片最大宽度
    const cardHeight = 600; // 卡片最大高度
    const padding = 10;

    let finalX = x;
    let finalY = y;

    // 水平方向：如果超出右边界，显示在左侧
    if (x + cardWidth > rect.right - padding) {
      finalX = x - cardWidth - padding;
    }
    // 如果超出左边界，显示在右侧
    if (finalX < rect.left + padding) {
      finalX = rect.left + padding;
    }

    // 垂直方向：如果超出下边界，显示在上方
    if (y + cardHeight > rect.bottom - padding) {
      finalY = y - cardHeight - padding;
    }
    // 如果超出上边界，显示在下方
    if (finalY < rect.top + padding) {
      finalY = rect.top + padding;
    }

    return { x: finalX - rect.left, y: finalY - rect.top };
  };

  const adjustedPosition = detailCardVisible
    ? calculateCardPosition(detailCardPosition.x, detailCardPosition.y)
    : { x: 0, y: 0 };

  // 点击外部区域关闭卡片
  useEffect(() => {
    if (!detailCardVisible) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (chartContainerRef.current && !chartContainerRef.current.contains(e.target as Node)) {
        // 检查是否点击在卡片上
        const target = e.target as HTMLElement;
        if (!target.closest('.trade-detail-card')) {
          setDetailCardVisible(false);
          setFocusMode(false);
          setFocusedIndicators([]);
          if (onOrderSelect) onOrderSelect(null);
          if (onDecisionSelect) onDecisionSelect(0);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [detailCardVisible, onOrderSelect, onDecisionSelect]);

  return (
    <div style={{ position: 'relative', width: '100%', height: `${height}px` }}>
      <div style={{ width: '100%', height: `${height}px` }} ref={chartContainerRef} />
      {detailCardVisible && (
        <TradeDetailCard
          order={detailCardOrder}
          decision={detailCardDecision}
          bar={detailCardBar}
          bars={bars}
          position={adjustedPosition}
          onClose={() => {
            setDetailCardVisible(false);
            setFocusMode(false);
            setFocusedIndicators([]);
            if (onOrderSelect) onOrderSelect(null);
            if (onDecisionSelect) onDecisionSelect(0);
          }}
        />
      )}
      {focusMode && (
        <div
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            padding: '8px 16px',
            backgroundColor: '#fff',
            border: '1px solid #e0e0e0',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            zIndex: 1001,
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
          onClick={() => {
            setFocusMode(false);
            setFocusedIndicators([]);
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f5f5f5';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#fff';
          }}
        >
          显示全部指标
        </div>
      )}
    </div>
  );
}

