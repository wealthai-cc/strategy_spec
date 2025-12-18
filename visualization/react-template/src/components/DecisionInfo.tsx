/**
 * 决策信息组件
 * 
 * 显示策略决策的详细信息
 */

import type { DecisionInfo as DecisionInfoType } from '../types/data';

interface DecisionInfoProps {
  decisions: DecisionInfoType[];
  selectedTimestamp?: number;
  onSelect?: (timestamp: number) => void;
}

export function DecisionInfo({ decisions, selectedTimestamp, onSelect }: DecisionInfoProps) {
  const selectedDecision = decisions.find(d => d.timestamp === selectedTimestamp);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '300px 1fr',
      gap: '20px',
      height: '400px',
    }}>
      {/* 决策列表 */}
      <div style={{
        overflowY: 'auto',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '12px',
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
          决策时间线 ({decisions.length})
        </h3>
        {decisions.map((decision, index) => {
          const isSelected = decision.timestamp === selectedTimestamp;
          const date = new Date(decision.timestamp);
          
          return (
            <div
              key={index}
              onClick={() => onSelect?.(decision.timestamp)}
              style={{
                padding: '12px',
                marginBottom: '8px',
                backgroundColor: isSelected ? '#e3f2fd' : '#ffffff',
                border: `1px solid ${isSelected ? '#2196F3' : '#e0e0e0'}`,
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <div style={{
                fontSize: '12px',
                color: '#666',
                marginBottom: '4px',
              }}>
                {date.toLocaleString()}
              </div>
              <div style={{
                fontSize: '14px',
                fontWeight: 'bold',
                color: decision.decision_type === 'buy' ? '#26a69a' : 
                       decision.decision_type === 'sell' ? '#ef5350' : '#666',
              }}>
                {decision.decision_type.toUpperCase()}
              </div>
              {decision.decision_reason && (
                <div style={{
                  fontSize: '12px',
                  color: '#666',
                  marginTop: '4px',
                }}>
                  {decision.decision_reason}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 决策详情 */}
      <div style={{
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '20px',
        overflowY: 'auto',
      }}>
        {selectedDecision ? (
          <>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
              决策详情
            </h3>
            
            <DetailSection title="基本信息">
              <DetailRow label="时间" value={new Date(selectedDecision.timestamp).toLocaleString()} />
              <DetailRow label="标的" value={selectedDecision.symbol} />
              <DetailRow label="决策类型" value={selectedDecision.decision_type.toUpperCase()} />
            </DetailSection>

            {Object.keys(selectedDecision.indicators).length > 0 && (
              <DetailSection title="技术指标">
                {Object.entries(selectedDecision.indicators).map(([key, value]) => (
                  <DetailRow key={key} label={key} value={value} />
                ))}
              </DetailSection>
            )}

            {selectedDecision.trigger_condition && (
              <DetailSection title="触发条件">
                <DetailRow label="条件" value={selectedDecision.trigger_condition} />
                <DetailRow 
                  label="结果" 
                  value={selectedDecision.condition_result ? '✓ 满足' : '✗ 不满足'} 
                />
              </DetailSection>
            )}

            {selectedDecision.decision_reason && (
              <DetailSection title="决策依据">
                <div style={{ color: '#333', lineHeight: '1.6' }}>
                  {selectedDecision.decision_reason}
                </div>
              </DetailSection>
            )}

            {selectedDecision.strategy_state && (
              <DetailSection title="策略状态">
                {Object.entries(selectedDecision.strategy_state).map(([key, value]) => (
                  <DetailRow 
                    key={key} 
                    label={key} 
                    value={typeof value === 'object' ? JSON.stringify(value) : String(value)} 
                  />
                ))}
              </DetailSection>
            )}
          </>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#999',
          }}>
            请从左侧选择一个决策查看详情
          </div>
        )}
      </div>
    </div>
  );
}

interface DetailSectionProps {
  title: string;
  children: React.ReactNode;
}

function DetailSection({ title, children }: DetailSectionProps) {
  return (
    <div style={{ marginBottom: '20px' }}>
      <h4 style={{
        margin: '0 0 12px 0',
        fontSize: '14px',
        fontWeight: 'bold',
        color: '#666',
        borderBottom: '1px solid #e0e0e0',
        paddingBottom: '8px',
      }}>
        {title}
      </h4>
      {children}
    </div>
  );
}

interface DetailRowProps {
  label: string;
  value: string;
}

function DetailRow({ label, value }: DetailRowProps) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      padding: '8px 0',
      fontSize: '14px',
    }}>
      <span style={{ color: '#666', fontWeight: '500' }}>{label}:</span>
      <span style={{ color: '#333' }}>{value}</span>
    </div>
  );
}

