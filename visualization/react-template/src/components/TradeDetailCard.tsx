/**
 * 买卖点详情卡片组件
 * 
 * 显示买卖点的完整决策信息，包括：
 * - 订单基本信息
 * - 触发条件
 * - 判断结果
 * - 技术指标值
 * - 决策依据
 * - 策略状态
 * - 上下文数据（可折叠）
 */

import { useState, memo } from 'react';
import type { OrderData, DecisionInfo, BarData } from '../types/data';
import './TradeDetailCard.css';

interface TradeDetailCardProps {
  order?: OrderData;
  decision?: DecisionInfo;
  bar?: BarData;
  bars?: BarData[]; // 用于上下文数据
  position: { x: number; y: number };
  onClose: () => void;
}

export const TradeDetailCard = memo(function TradeDetailCard({
  order,
  decision,
  bar,
  bars = [],
  position,
  onClose,
}: TradeDetailCardProps) {
  const [contextExpanded, setContextExpanded] = useState(false);

  if (!order && !decision) {
    return null;
  }

  // 确定方向
  const direction = order?.direction || decision?.decision_type || 'buy';
  const isBuy = direction === 'buy';

  // 获取触发条件和判断结果
  const triggerCondition = decision?.trigger_condition || order?.trigger_reason || null;
  const conditionResult = decision?.condition_result;
  const decisionReason = decision?.decision_reason || null;

  // 获取技术指标
  const indicators = decision?.indicators || bar?.indicators || {};

  // 获取策略状态
  const strategyState = decision?.strategy_state || null;

  // 计算上下文数据（前后3根K线）
  const contextBars: BarData[] = [];
  if (bar && bars.length > 0) {
    const currentIndex = bars.findIndex(b => b.open_time === bar.open_time);
    if (currentIndex >= 0) {
      const startIndex = Math.max(0, currentIndex - 3);
      const endIndex = Math.min(bars.length - 1, currentIndex + 3);
      for (let i = startIndex; i <= endIndex; i++) {
        contextBars.push(bars[i]);
      }
    }
  }

  // 解析触发条件，提取价格和指标值
  const parseCondition = (condition: string | null) => {
    if (!condition) return null;
    
    // 尝试从条件中提取数值，例如 "price > MA5 * 1.01 (10.65 > 11.71)"
    const match = condition.match(/\(([\d.]+)\s*([><=]+)\s*([\d.]+)\)/);
    if (match) {
      return {
        leftValue: parseFloat(match[1]),
        operator: match[2],
        rightValue: parseFloat(match[3]),
        fullText: condition,
      };
    }
    
    return { fullText: condition };
  };

  const conditionInfo = parseCondition(triggerCondition);

  return (
    <div
      className="trade-detail-card"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
      }}
    >
      {/* 关闭按钮 */}
      <button className="trade-detail-card-close" onClick={onClose}>
        ×
      </button>

      {/* 头部：订单方向、价格、数量 */}
      <div className={`trade-detail-card-header ${isBuy ? 'buy' : 'sell'}`}>
        <div className="trade-detail-card-direction">
          {isBuy ? '买入' : '卖出'}
        </div>
        {order && (
          <div className="trade-detail-card-price-qty">
            <span className="price">{parseFloat(order.price).toFixed(2)}</span>
            <span className="qty">× {order.quantity}</span>
          </div>
        )}
      </div>

      {/* 触发条件 */}
      {triggerCondition && (
        <div className="trade-detail-card-section">
          <div className="section-title">触发条件</div>
          <div className="section-content">
            {conditionInfo?.fullText || triggerCondition}
          </div>
        </div>
      )}

      {/* 判断结果 */}
      {conditionResult !== null && conditionResult !== undefined && (
        <div className="trade-detail-card-section">
          <div className="section-title">判断结果</div>
          <div
            className={`section-content condition-result ${
              conditionResult ? 'satisfied' : 'not-satisfied'
            }`}
          >
            {conditionResult ? '✓ 满足' : '✗ 不满足'}
          </div>
          {conditionInfo && (
            <div className="section-content price-relation">
              {conditionInfo.leftValue !== undefined ? (
                <>
                  {conditionInfo.leftValue.toFixed(2)} {conditionInfo.operator}{' '}
                  {conditionInfo.rightValue.toFixed(2)}{' '}
                  <span className={conditionResult ? 'satisfied' : 'not-satisfied'}>
                    {conditionResult ? '✓' : '✗'}
                  </span>
                </>
              ) : (
                conditionInfo.fullText
              )}
            </div>
          )}
        </div>
      )}

      {/* 实际数据 */}
      {bar && (
        <div className="trade-detail-card-section">
          <div className="section-title">实际数据</div>
          <div className="section-content">
            <div className="data-row">
              <span className="data-label">当前价格:</span>
              <span className="data-value">{parseFloat(bar.close).toFixed(2)}</span>
            </div>
            {indicators.MA5 && (
              <div className="data-row">
                <span className="data-label">MA5值:</span>
                <span className="data-value">
                  {(() => {
                    const ma5Value = typeof indicators.MA5 === 'string' 
                      ? parseFloat(indicators.MA5) 
                      : (typeof indicators.MA5 === 'number' ? indicators.MA5 : 0);
                    return isNaN(ma5Value) ? 'N/A' : ma5Value.toFixed(2);
                  })()}
                </span>
              </div>
            )}
            {triggerCondition?.includes('MA5 * 1.01') && indicators.MA5 && (
              <div className="data-row">
                <span className="data-label">阈值(MA5*1.01):</span>
                <span className="data-value">
                  {(() => {
                    const ma5Value = typeof indicators.MA5 === 'string' 
                      ? parseFloat(indicators.MA5) 
                      : (typeof indicators.MA5 === 'number' ? indicators.MA5 : 0);
                    const threshold = ma5Value * 1.01;
                    return isNaN(threshold) ? 'N/A' : threshold.toFixed(2);
                  })()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 技术指标 */}
      {Object.keys(indicators).length > 0 && (
        <div className="trade-detail-card-section">
          <div className="section-title">技术指标</div>
          <div className="section-content">
            {Object.entries(indicators).map(([key, value]) => {
              const numValue = typeof value === 'string' ? parseFloat(value) : (typeof value === 'number' ? value : 0);
              return (
                <div key={key} className="data-row">
                  <span className="data-label">{key}:</span>
                  <span className="data-value">
                    {isNaN(numValue) ? 'N/A' : numValue.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 决策依据 */}
      {decisionReason && (
        <div className="trade-detail-card-section">
          <div className="section-title">决策依据</div>
          <div className="section-content">{decisionReason}</div>
        </div>
      )}

      {/* 策略状态 */}
      {strategyState && (
        <div className="trade-detail-card-section">
          <div className="section-title">策略状态</div>
          <div className="section-content">
            {Object.entries(strategyState).map(([key, value]) => {
              const numValue = typeof value === 'number' ? value : (typeof value === 'string' ? parseFloat(value) : 0);
              return (
                <div key={key} className="data-row">
                  <span className="data-label">{key}:</span>
                  <span className="data-value">
                    {typeof value === 'number' ? (isNaN(numValue) ? 'N/A' : numValue.toFixed(2)) : String(value)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 上下文数据（可折叠） */}
      {contextBars.length > 0 && (
        <div className="trade-detail-card-section">
          <div
            className="section-title clickable"
            onClick={() => setContextExpanded(!contextExpanded)}
          >
            上下文数据 {contextExpanded ? '▼' : '▶'}
          </div>
          {contextExpanded && (
            <div className="section-content context-table">
              <table>
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>开盘</th>
                    <th>收盘</th>
                    <th>最高</th>
                    <th>最低</th>
                    <th>成交量</th>
                    {indicators.MA5 && <th>MA5</th>}
                  </tr>
                </thead>
                <tbody>
                  {contextBars.map((b, idx) => {
                    const isCurrent = b.open_time === bar?.open_time;
                    return (
                      <tr key={idx} className={isCurrent ? 'current-bar' : ''}>
                        <td>{new Date(b.open_time).toLocaleDateString()}</td>
                        <td>{parseFloat(b.open).toFixed(2)}</td>
                        <td>{parseFloat(b.close).toFixed(2)}</td>
                        <td>{parseFloat(b.high).toFixed(2)}</td>
                        <td>{parseFloat(b.low).toFixed(2)}</td>
                        <td>{parseFloat(b.volume).toLocaleString()}</td>
                        {indicators.MA5 && (
                          <td>
                            {b.indicators?.MA5
                              ? parseFloat(b.indicators.MA5).toFixed(2)
                              : 'N/A'}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

