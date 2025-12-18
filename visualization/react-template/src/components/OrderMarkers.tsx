/**
 * 订单标记组件
 * 
 * 在图表上显示买卖点标记（已集成到 KLineChart 中）
 * 此组件用于显示订单详情面板
 */

import type { OrderData } from '../types/data';

interface OrderMarkersProps {
  orders: OrderData[];
  selectedOrderId?: string | null;
  onSelect?: (orderId: string | null) => void;
}

export function OrderMarkers({ orders, selectedOrderId, onSelect }: OrderMarkersProps) {
  const selectedOrder = orders.find(o => o.order_id === selectedOrderId);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '300px 1fr',
      gap: '20px',
      height: '300px',
    }}>
      {/* 订单列表 */}
      <div style={{
        overflowY: 'auto',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '12px',
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
          订单列表 ({orders.length})
        </h3>
        {orders.map((order, index) => {
          const isSelected = order.order_id === selectedOrderId;
          const date = new Date(order.timestamp);
          const color = order.direction === 'buy' ? '#26a69a' : '#ef5350';
          
          return (
            <div
              key={order.order_id || index}
              onClick={() => onSelect?.(order.order_id || null)}
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
                color: color,
                marginBottom: '4px',
              }}>
                {order.direction.toUpperCase()} {order.quantity} @ {order.price}
              </div>
              <div style={{
                fontSize: '12px',
                color: '#666',
              }}>
                {order.order_type} · {order.status}
              </div>
            </div>
          );
        })}
      </div>

      {/* 订单详情 */}
      <div style={{
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '20px',
        overflowY: 'auto',
      }}>
        {selectedOrder ? (
          <>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
              订单详情
            </h3>
            
            <DetailSection title="基本信息">
              <DetailRow label="订单ID" value={selectedOrder.order_id || 'N/A'} />
              <DetailRow label="时间" value={new Date(selectedOrder.timestamp).toLocaleString()} />
              <DetailRow label="标的" value={selectedOrder.symbol} />
              <DetailRow 
                label="方向" 
                value={selectedOrder.direction.toUpperCase()} 
                color={selectedOrder.direction === 'buy' ? '#26a69a' : '#ef5350'}
              />
            </DetailSection>

            <DetailSection title="交易信息">
              <DetailRow label="价格" value={selectedOrder.price} />
              <DetailRow label="数量" value={String(selectedOrder.quantity)} />
              <DetailRow label="订单类型" value={selectedOrder.order_type} />
              <DetailRow label="状态" value={selectedOrder.status} />
            </DetailSection>

            {selectedOrder.trigger_reason && (
              <DetailSection title="触发原因">
                <div style={{ color: '#333', lineHeight: '1.6' }}>
                  {selectedOrder.trigger_reason}
                </div>
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
            请从左侧选择一个订单查看详情
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
  color?: string;
}

function DetailRow({ label, value, color }: DetailRowProps) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      padding: '8px 0',
      fontSize: '14px',
    }}>
      <span style={{ color: '#666', fontWeight: '500' }}>{label}:</span>
      <span style={{ color: color || '#333' }}>{value}</span>
    </div>
  );
}

