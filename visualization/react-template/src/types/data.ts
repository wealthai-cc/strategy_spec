/**
 * 策略测试数据格式类型定义
 * 
 * 对应 Python 导出的 JSON 数据格式
 */

export interface StrategyData {
  version: string;
  metadata: Metadata;
  bars: BarData[];
  orders: OrderData[];
  decisions: DecisionInfo[];
  statistics: Statistics;
  framework_verification?: FrameworkVerification;
  strategy_analysis?: StrategyAnalysis;
}

export interface Metadata {
  strategy_name: string;
  symbol: string;
  market_type: string;
  test_start_time: string | null;
  test_end_time: string | null;
  timeframe: string;
}

export interface BarData {
  open_time: number;
  close_time: number;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

export interface OrderData {
  order_id: string | null;
  symbol: string;
  direction: string; // 'buy' | 'sell'
  price: string;
  quantity: number;
  timestamp: number;
  order_type: string;
  status: string;
  trigger_reason: string | null;
}

export interface DecisionInfo {
  timestamp: number;
  symbol: string;
  decision_type: string; // 'buy' | 'sell' | 'hold'
  indicators: Record<string, string>;
  trigger_condition: string | null;
  condition_result: boolean | null;
  decision_reason: string | null;
  strategy_state: Record<string, any> | null;
}

export interface Statistics {
  total_orders: number;
  buy_orders: number;
  sell_orders: number;
  total_bars: number;
  total_decisions: number;
}

export interface FrameworkVerification {
  checks: FrameworkCheck[];
  overall_status: boolean | null;
  total_checks: number;
  passed_checks: number;
}

export interface FrameworkCheck {
  feature_name: string;
  status: boolean;
  details: string | null;
}

export interface StrategyAnalysis {
  execution_status: 'success' | 'no_orders' | 'no_data';
  order_statistics: {
    total: number;
    buy: number;
    sell: number;
  };
  data_validation: {
    has_bars: boolean;
    has_orders: boolean;
    has_decisions: boolean;
    bar_count: number;
  };
  errors: string[];
  warnings: string[];
}

