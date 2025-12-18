/**
 * 框架验证面板组件
 * 
 * 显示策略框架功能验证结果，包括：
 * - 框架功能列表（g、log、run_daily 等）
 * - 功能状态（正常/异常）
 * - 错误信息（如果有）
 */

import React from 'react';
import type { FrameworkVerification } from '../types/data';
import './FrameworkVerification.css';

interface FrameworkVerificationProps {
  data: FrameworkVerification | undefined;
}

export const FrameworkVerificationPanel: React.FC<FrameworkVerificationProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="framework-verification">
        <h3>框架验证</h3>
        <p className="no-data">暂无框架验证数据</p>
      </div>
    );
  }

  const { checks, overall_status, total_checks, passed_checks } = data;

  return (
    <div className="framework-verification">
      <h3>框架验证</h3>
      
      {/* 总体状态 */}
      <div className="verification-summary">
        <div className={`status-badge ${overall_status === true ? 'success' : overall_status === false ? 'error' : 'unknown'}`}>
          {overall_status === true ? '✅ 通过' : overall_status === false ? '❌ 失败' : '⚠️ 未知'}
        </div>
        <div className="summary-text">
          {passed_checks} / {total_checks} 项检查通过
        </div>
      </div>

      {/* 功能检查列表 */}
      <div className="checks-list">
        {checks.length === 0 ? (
          <p className="no-data">暂无检查项</p>
        ) : (
          checks.map((check, index) => (
            <div key={index} className={`check-item ${check.status ? 'success' : 'error'}`}>
              <div className="check-header">
                <span className="check-icon">
                  {check.status ? '✅' : '❌'}
                </span>
                <span className="check-name">{check.feature_name}</span>
              </div>
              {check.details && (
                <div className="check-details">{check.details}</div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

