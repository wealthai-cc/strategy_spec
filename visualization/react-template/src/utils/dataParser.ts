/**
 * 数据解析工具函数
 */

import type { StrategyData, BarData, OrderData } from '../types/data';

/**
 * 解析 JSON 数据文件
 */
export function parseStrategyData(jsonData: any): StrategyData {
  // 验证数据格式
  if (!jsonData.version || !jsonData.metadata) {
    throw new Error('Invalid data format: missing version or metadata');
  }

  return jsonData as StrategyData;
}

/**
 * 将 BarData 转换为 TradingView 图表格式
 */
export function convertBarsToChartData(bars: BarData[]) {
  return bars.map(bar => ({
    time: bar.open_time / 1000, // TradingView 使用秒级时间戳
    open: parseFloat(bar.open),
    high: parseFloat(bar.high),
    low: parseFloat(bar.low),
    close: parseFloat(bar.close),
    volume: parseFloat(bar.volume),
  }));
}

/**
 * 将订单数据转换为图表标记格式
 */
export function convertOrdersToMarkers(orders: OrderData[]) {
  return orders.map(order => ({
    time: order.timestamp / 1000,
    position: order.direction === 'buy' ? 'belowBar' : 'aboveBar',
    color: order.direction === 'buy' ? '#26a69a' : '#ef5350',
    shape: order.direction === 'buy' ? 'arrowUp' : 'arrowDown',
    text: `${order.direction.toUpperCase()} ${order.quantity}@${order.price}`,
    size: 1,
  }));
}

