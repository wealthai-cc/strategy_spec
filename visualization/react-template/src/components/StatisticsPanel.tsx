/**
 * 统计面板组件
 * 
 * 显示策略测试的统计信息
 */

import type { Statistics, Metadata } from '../types/data';

interface StatisticsPanelProps {
  statistics: Statistics;
  metadata: Metadata;
}

export function StatisticsPanel({ statistics, metadata }: StatisticsPanelProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '16px',
      padding: '20px',
      backgroundColor: '#f9f9f9',
      borderRadius: '8px',
      marginBottom: '20px',
    }}>
      {/* 策略信息 */}
      <div style={{
        gridColumn: '1 / -1',
        paddingBottom: '16px',
        borderBottom: '1px solid #e0e0e0',
      }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: 'bold' }}>
          {metadata.strategy_name}
        </h3>
        <div style={{ display: 'flex', gap: '16px', fontSize: '14px', color: '#666' }}>
          <span>标的: {metadata.symbol}</span>
          <span>市场: {metadata.market_type}</span>
          <span>周期: {metadata.timeframe}</span>
        </div>
      </div>

      {/* 统计卡片 */}
      <StatCard
        label="总交易次数"
        value={statistics.total_orders}
        color="#2196F3"
      />
      <StatCard
        label="买入次数"
        value={statistics.buy_orders}
        color="#26a69a"
      />
      <StatCard
        label="卖出次数"
        value={statistics.sell_orders}
        color="#ef5350"
      />
      <StatCard
        label="K线数量"
        value={statistics.total_bars}
        color="#FF9800"
      />
      <StatCard
        label="决策次数"
        value={statistics.total_decisions}
        color="#9C27B0"
      />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  color: string;
}

function StatCard({ label, value, color }: StatCardProps) {
  return (
    <div style={{
      padding: '16px',
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      textAlign: 'center',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    }}>
      <div style={{
        fontSize: '32px',
        fontWeight: 'bold',
        color: color,
        marginBottom: '8px',
      }}>
        {value}
      </div>
      <div style={{
        fontSize: '14px',
        color: '#666',
      }}>
        {label}
      </div>
    </div>
  );
}

