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
  risk_reward_planned: number;
  risk_reward_realized: number;
  exit_reason: string;
};

export type BacktestResult = {
  portfolio: Portfolio;
  performance: Performance;
  signals: Signal[];
  rejected: { symbol: string; reasons: string[] }[];
  trades: Trade[];
};

