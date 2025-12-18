/**
 * 主应用组件
 * 
 * 集成所有子组件，实现完整的策略测试可视化界面
 */

import { useState } from 'react';
import { useDataLoader } from './hooks/useDataLoader';
import { KLineChartECharts } from './components/KLineChartECharts';
import { StatisticsPanel } from './components/StatisticsPanel';
import { DecisionInfo } from './components/DecisionInfo';
import { OrderMarkers } from './components/OrderMarkers';
import { FrameworkVerificationPanel } from './components/FrameworkVerification';
import { StrategyAnalysisPanel } from './components/StrategyAnalysis';
import './App.css';

function App() {
  const { data, loading, error } = useDataLoader();
  const [selectedDecisionTimestamp, setSelectedDecisionTimestamp] = useState<number | undefined>();
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);

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
            请确保已运行策略测试，数据文件应位于: public/latest_report.json
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
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
        <div style={{ color: '#666', textAlign: 'center', maxWidth: '500px' }}>
          正在加载数据...
        </div>
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

        {/* 统计面板 */}
        <StatisticsPanel 
          statistics={data.statistics} 
          metadata={data.metadata} 
        />

        {/* K 线图表 - 优先展示 */}
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
          <KLineChartECharts
            bars={data.bars}
            orders={data.orders}
            decisions={data.decisions}
            height={500}
            selectedOrderId={selectedOrderId}
            selectedDecisionTimestamp={selectedDecisionTimestamp}
            onOrderSelect={setSelectedOrderId}
            onDecisionSelect={setSelectedDecisionTimestamp}
          />
        </div>

        {/* 决策信息 - 决策归因，优先展示 */}
        {data.decisions.length > 0 && (
          <div style={{
            marginBottom: '20px',
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}>
            <h2 style={{ margin: '0 0 16px 0', fontSize: '20px', fontWeight: 'bold' }}>
              策略决策归因
            </h2>
            <DecisionInfo
              decisions={data.decisions}
              selectedTimestamp={selectedDecisionTimestamp}
              onSelect={setSelectedDecisionTimestamp}
            />
          </div>
        )}

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

        {/* 框架验证面板 - 移到底部 */}
        {data.framework_verification && (
          <FrameworkVerificationPanel data={data.framework_verification} />
        )}

        {/* 策略分析面板 - 移到底部 */}
        {data.strategy_analysis && (
          <StrategyAnalysisPanel data={data.strategy_analysis} />
        )}
      </div>
    </div>
  );
}

export default App;
