import type { BacktestRequest, BacktestResult } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function runBacktest(request: BacktestRequest): Promise<BacktestResult> {
  const params = new URLSearchParams({
    symbol: request.symbol,
    initialCapital: String(request.initialCapital),
    provider: request.provider,
    start: request.start,
    end: request.end,
    timeframe: request.timeframe
  });
  if (request.apiKey) {
    params.set("apiKey", request.apiKey);
  }
  const response = await fetch(`${API_BASE}/api/simulation/backtest?${params.toString()}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Backtest failed with ${response.status}`);
  }
  return response.json();
}
