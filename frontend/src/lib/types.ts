export type Portfolio = {
  initialCapital: number;
  cash: number;
  equity: number;
  realizedPnl: number;
  totalReturnPct: number;
};

export type Performance = {
  trades: number;
  winRate: number;
  grossProfit: number;
  grossLoss: number;
  profitFactor: number | null;
  netProfit: number;
};

export type Signal = {
  symbol: string;
  strategy_name: string;
  decision: string;
  confidence: number;
  entry_price: number;
  stop_price: number;
  target_price: number;
  risk_reward_ratio: number;
  score: number;
  crowding_score: number;
  trap_risk_score: number;
  entry_quality: string;
  status: string;
  reasons: string[];
};

export type Trade = {
  symbol: string;
  strategy: string;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  shares: number;
  gross_pnl: number;
  net_pnl: number;
  fees: number;
  slippage: number;
  risk_amount: number;
  reward_amount: number;
  risk_reward_planned: number;
  risk_reward_realized: number;
  exit_reason: string;
};

export type Candle = {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timeframe: string;
  vwap?: number | null;
};

export type BacktestResult = {
  portfolio: Portfolio;
  performance: Performance;
  signals: Signal[];
  rejected: { symbol: string; reasons: string[] }[];
  trades: Trade[];
  candles: Candle[];
  dataSource?: {
    provider: string;
    source: string;
    symbol: string;
    timeframe: string;
    start: string;
    end: string;
    candles: number;
    warning: string | null;
  };
};

export type BacktestRequest = {
  symbol: string;
  initialCapital: number;
  provider: string;
  start: string;
  end: string;
  timeframe: string;
  apiKey?: string;
};

export type Opportunity = {
  rank: number;
  symbol: string;
  status: string;
  opportunity_score: number;
  momentum_score: number;
  setup_score: number;
  liquidity_score: number;
  best_strategy: string;
  decision: string;
  entry_price: number;
  stop_price: number;
  target_price: number;
  risk_reward_ratio: number;
  return_20d_pct: number;
  return_50d_pct: number;
  relative_volume: number;
  rsi: number;
  reasons: string[];
  data_warning: string | null;
};

export type OpportunityScanRequest = {
  universe?: string;
  symbols?: string;
  includeEtfs?: boolean;
  maxSymbols?: number;
  provider: string;
  start: string;
  end: string;
  timeframe: string;
  limit?: number;
  apiKey?: string;
};

export type OpportunityScanResult = {
  universe: string;
  universeSize: number;
  provider: string;
  timeframe: string;
  start: string;
  end: string;
  opportunities: Opportunity[];
};
