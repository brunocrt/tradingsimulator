import type { BacktestResult } from "./types";

export const sampleResult: BacktestResult = {
  portfolio: {
    initialCapital: 10000,
    cash: 10030.33,
    equity: 10030.33,
    realizedPnl: 30.33,
    totalReturnPct: 0.3
  },
  performance: {
    trades: 2,
    winRate: 100,
    grossProfit: 30.33,
    grossLoss: 0,
    profitFactor: null,
    netProfit: 30.33
  },
  signals: [
    {
      symbol: "AMD",
      strategy_name: "VWAP_PULLBACK",
      decision: "BUY",
      confidence: 0.82,
      entry_price: 125.18,
      stop_price: 124.68,
      target_price: 126.03,
      risk_reward_ratio: 1.7,
      score: 82,
      crowding_score: 35,
      trap_risk_score: 20,
      entry_quality: "GOOD",
      status: "APPROVED",
      reasons: ["VWAP pullback held, spread stayed tight, and risk/reward passed the threshold"]
    },
    {
      symbol: "AMD",
      strategy_name: "OPENING_RANGE_BREAKOUT",
      decision: "WAIT",
      confidence: 0.58,
      entry_price: 127.35,
      stop_price: 125.84,
      target_price: 130.36,
      risk_reward_ratio: 2,
      score: 58,
      crowding_score: 65,
      trap_risk_score: 35,
      entry_quality: "POOR",
      status: "WAIT",
      reasons: ["Anti-chase overlay detected extension after the breakout"]
    }
  ],
  rejected: [],
  trades: [
    {
      symbol: "AMD",
      strategy: "VWAP_PULLBACK",
      entry_time: "2026-05-26T10:25:00",
      exit_time: "2026-05-26T10:32:00",
      entry_price: 125.2401,
      exit_price: 126.0396,
      shares: 19,
      gross_pnl: 15.19,
      net_pnl: 15.17,
      fees: 0.0223,
      slippage: 0.0504,
      risk_amount: 9.5,
      reward_amount: 16.15,
      risk_reward_planned: 1.7,
      risk_reward_realized: 1.6,
      exit_reason: "TAKE_PROFIT"
    },
    {
      symbol: "AMD",
      strategy: "VWAP_PULLBACK",
      entry_time: "2026-05-26T11:15:00",
      exit_time: "2026-05-26T11:22:00",
      entry_price: 125.6602,
      exit_price: 126.4594,
      shares: 19,
      gross_pnl: 15.18,
      net_pnl: 15.16,
      fees: 0.0224,
      slippage: 0.0506,
      risk_amount: 9.5,
      reward_amount: 16.15,
      risk_reward_planned: 1.7,
      risk_reward_realized: 1.6,
      exit_reason: "TAKE_PROFIT"
    }
  ],
  candles: Array.from({ length: 80 }, (_, index) => {
    const base = 124 + index * 0.06 + Math.sin(index / 5) * 0.35;
    return {
      symbol: "AMD",
      timestamp: new Date(Date.UTC(2026, 4, 26, 13, 30 + index)).toISOString(),
      open: Number((base - 0.08).toFixed(2)),
      high: Number((base + 0.28).toFixed(2)),
      low: Number((base - 0.24).toFixed(2)),
      close: Number((base + 0.08).toFixed(2)),
      volume: 180000 + index * 1200,
      timeframe: "1m",
      vwap: null
    };
  }),
  dataSource: {
    provider: "sample",
    source: "generated sample candles",
    symbol: "AMD",
    timeframe: "1m",
    start: "2026-05-26",
    end: "2026-05-26",
    candles: 180,
    warning: null
  }
};
