/**
 * 主应用组件
 * 
 * 集成所有子组件，实现完整的策略测试可视化界面
 */

import { useState } from 'react';
import { useDataLoader } from './hooks/useDataLoader';
import { KLineChart } from './components/KLineChart';
import { StatisticsPanel } from './components/StatisticsPanel';
import { DecisionInfo } from './components/DecisionInfo';
import { OrderMarkers } from './components/OrderMarkers';
import { FrameworkVerificationPanel } from './components/FrameworkVerification';
import { StrategyAnalysisPanel } from './components/StrategyAnalysis';
import './App.css';

function App() {
  const { data, loading, error, loadFromFile } = useDataLoader();
  const [selectedDecisionTimestamp, setSelectedDecisionTimestamp] = useState<number | undefined>();
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      loadFromFile(file);
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '16px',
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #2196F3',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }} />
        <div style={{ color: '#666' }}>加载数据中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '16px',
        padding: '20px',
        backgroundColor: '#f5f5f5',
      }}>
        <div style={{ color: '#ef5350', fontSize: '18px', fontWeight: 'bold' }}>
          ❌ 加载失败
        </div>
        <div style={{ color: '#666', textAlign: 'center', maxWidth: '500px', backgroundColor: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
          <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>错误信息：</div>
          <div style={{ marginBottom: '16px', fontFamily: 'monospace', fontSize: '12px' }}>{error}</div>
          <div style={{ fontSize: '12px', color: '#999', marginTop: '16px' }}>
            当前 URL: {window.location.href}
          </div>
        </div>
        <div style={{ marginTop: '20px' }}>
          <input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          />
        </div>
      </div>
    );
  }

  if (!data) {
    const urlParams = new URLSearchParams(window.location.search);
    const dataUrl = urlParams.get('data');
    
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '20px',
        padding: '20px',
        backgroundColor: '#f5f5f5',
      }}>
        <h1 style={{ margin: 0, fontSize: '24px', color: '#333' }}>
          策略测试可视化
        </h1>
        {dataUrl ? (
          <div style={{ color: '#666', textAlign: 'center', maxWidth: '500px', backgroundColor: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
            <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>正在加载数据...</div>
            <div style={{ fontSize: '12px', color: '#999', fontFamily: 'monospace', wordBreak: 'break-all' }}>
              {dataUrl}
            </div>
            {loading && (
              <div style={{ marginTop: '16px', color: '#2196F3' }}>
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '3px solid #f3f3f3',
                  borderTop: '3px solid #2196F3',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto',
                }} />
              </div>
            )}
          </div>
        ) : (
          <>
            <div style={{ color: '#666', textAlign: 'center', maxWidth: '500px' }}>
              请上传 JSON 数据文件或通过 URL 参数加载数据
            </div>
            <div>
              <input
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                style={{
                  padding: '10px 20px',
                  fontSize: '16px',
                  cursor: 'pointer',
                  border: '2px solid #2196F3',
                  borderRadius: '4px',
                  backgroundColor: '#fff',
                }}
              />
            </div>
            <div style={{ fontSize: '12px', color: '#999', marginTop: '20px' }}>
              提示：也可以通过 URL 参数加载数据，例如：?data=path/to/data.json
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      padding: '20px',
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
      }}>
        {/* 头部 */}
        <div style={{
          marginBottom: '20px',
          padding: '20px',
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        }}>
          <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', color: '#333' }}>
            策略测试可视化报告
          </h1>
          <div style={{ fontSize: '14px', color: '#666' }}>
            数据版本: {data.version} | 
            测试时间: {data.metadata.test_start_time ? 
              new Date(data.metadata.test_start_time).toLocaleString() : 'N/A'}
          </div>
        </div>

        {/* 框架验证面板 */}
        {data.framework_verification && (
          <FrameworkVerificationPanel data={data.framework_verification} />
        )}

        {/* 策略分析面板 */}
        {data.strategy_analysis && (
          <StrategyAnalysisPanel data={data.strategy_analysis} />
        )}

        {/* 统计面板 */}
        <StatisticsPanel 
          statistics={data.statistics} 
          metadata={data.metadata} 
        />

        {/* K 线图表 */}
        <div style={{
          marginBottom: '20px',
          padding: '20px',
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        }}>
          <h2 style={{ margin: '0 0 16px 0', fontSize: '20px', fontWeight: 'bold' }}>
            K 线图表
          </h2>
          <KLineChart
            bars={data.bars}
            orders={data.orders}
            decisions={data.decisions}
            height={500}
          />
        </div>

        {/* 订单标记 */}
        {data.orders.length > 0 && (
          <div style={{
            marginBottom: '20px',
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}>
            <h2 style={{ margin: '0 0 16px 0', fontSize: '20px', fontWeight: 'bold' }}>
              订单详情
            </h2>
            <OrderMarkers
              orders={data.orders}
              selectedOrderId={selectedOrderId}
              onSelect={setSelectedOrderId}
            />
          </div>
        )}

        {/* 决策信息 */}
        {data.decisions.length > 0 && (
          <div style={{
            marginBottom: '20px',
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}>
            <h2 style={{ margin: '0 0 16px 0', fontSize: '20px', fontWeight: 'bold' }}>
              策略决策
            </h2>
            <DecisionInfo
              decisions={data.decisions}
              selectedTimestamp={selectedDecisionTimestamp}
              onSelect={setSelectedDecisionTimestamp}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
