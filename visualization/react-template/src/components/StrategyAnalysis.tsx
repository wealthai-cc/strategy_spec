/**
 * 策略分析面板组件
 * 
 * 显示策略执行分析结果，包括：
 * - 执行状态（成功/失败）
 * - 订单统计
 * - 数据验证结果
 * - 错误和警告列表
 */

import React from 'react';
import type { StrategyAnalysis } from '../types/data';
import './StrategyAnalysis.css';

interface StrategyAnalysisProps {
  data: StrategyAnalysis | undefined;
}

export const StrategyAnalysisPanel: React.FC<StrategyAnalysisProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="strategy-analysis">
        <h3>策略分析</h3>
        <p className="no-data">暂无策略分析数据</p>
      </div>
    );
  }

  const { execution_status, order_statistics, data_validation, errors, warnings } = data;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return '✅';
      case 'no_orders':
        return '⚠️';
      case 'no_data':
        return '❌';
      default:
        return '❓';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success':
        return '执行成功';
      case 'no_orders':
        return '无订单生成';
      case 'no_data':
        return '无数据';
      default:
        return '未知状态';
    }
  };

  return (
    <div className="strategy-analysis">
      <h3>策略分析</h3>

      {/* 执行状态 */}
      <div className="analysis-section">
        <h4>执行状态</h4>
        <div className={`status-indicator ${execution_status}`}>
          <span className="status-icon">{getStatusIcon(execution_status)}</span>
          <span className="status-text">{getStatusText(execution_status)}</span>
        </div>
      </div>

      {/* 订单统计 */}
      <div className="analysis-section">
        <h4>订单统计</h4>
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-label">总订单数</div>
            <div className="stat-value">{order_statistics.total}</div>
          </div>
          <div className="stat-item buy">
            <div className="stat-label">买入</div>
            <div className="stat-value">{order_statistics.buy}</div>
          </div>
          <div className="stat-item sell">
            <div className="stat-label">卖出</div>
            <div className="stat-value">{order_statistics.sell}</div>
          </div>
        </div>
      </div>

      {/* 数据验证 */}
      <div className="analysis-section">
        <h4>数据验证</h4>
        <div className="validation-list">
          <div className={`validation-item ${data_validation.has_bars ? 'success' : 'error'}`}>
            <span className="validation-icon">{data_validation.has_bars ? '✅' : '❌'}</span>
            <span className="validation-text">K线数据: {data_validation.bar_count} 条</span>
          </div>
          <div className={`validation-item ${data_validation.has_orders ? 'success' : 'warning'}`}>
            <span className="validation-icon">{data_validation.has_orders ? '✅' : '⚠️'}</span>
            <span className="validation-text">订单数据: {data_validation.has_orders ? '有' : '无'}</span>
          </div>
          <div className={`validation-item ${data_validation.has_decisions ? 'success' : 'warning'}`}>
            <span className="validation-icon">{data_validation.has_decisions ? '✅' : '⚠️'}</span>
            <span className="validation-text">决策数据: {data_validation.has_decisions ? '有' : '无'}</span>
          </div>
        </div>
      </div>

      {/* 错误列表 */}
      {errors.length > 0 && (
        <div className="analysis-section">
          <h4>错误信息</h4>
          <div className="message-list error-list">
            {errors.map((error, index) => (
              <div key={index} className="message-item error">
                <span className="message-icon">❌</span>
                <span className="message-text">{error}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 警告列表 */}
      {warnings.length > 0 && (
        <div className="analysis-section">
          <h4>警告信息</h4>
          <div className="message-list warning-list">
            {warnings.map((warning, index) => (
              <div key={index} className="message-item warning">
                <span className="message-icon">⚠️</span>
                <span className="message-text">{warning}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

