import type { BacktestResult } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function runBacktest(symbol: string, initialCapital: number): Promise<BacktestResult> {
  const params = new URLSearchParams({
    symbol,
    initialCapital: String(initialCapital)
  });
  const response = await fetch(`${API_BASE}/api/simulation/backtest?${params.toString()}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Backtest failed with ${response.status}`);
  }
  return response.json();
}
