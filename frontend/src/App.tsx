import { useEffect, useMemo, useState } from "react";
import { MetricTile } from "./components/MetricTile";
import { ScannerTable } from "./components/ScannerTable";
import { TradeJournal } from "./components/TradeJournal";
import { runBacktest } from "./lib/api";
import { sampleResult } from "./lib/sampleResult";
import type { BacktestResult } from "./lib/types";
import "./styles.css";

const SYMBOLS = ["AMD", "NVDA", "AAPL", "MSFT", "TSLA", "SPY"];
const DEFAULT_INITIAL_CAPITAL = 1000;

function dollars(value: number) {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export default function App() {
  const [symbol, setSymbol] = useState("AMD");
  const [initialCapital, setInitialCapital] = useState(DEFAULT_INITIAL_CAPITAL);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    runBacktest(symbol, initialCapital)
      .then(setResult)
      .catch((err: unknown) => {
        setResult(sampleResult);
        console.info("Using bundled sample backtest because the API is unavailable.", err);
      })
      .finally(() => setLoading(false));
  }, [symbol, initialCapital]);

  const tone = useMemo(() => {
    if (!result) return "neutral";
    return result.portfolio.realizedPnl >= 0 ? "good" : "bad";
  }, [result]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Trading Simulator</h1>
          <p>Risk-first backtesting and paper-trading research workspace</p>
        </div>
        <div className="controls">
          <div className="field">
            <label htmlFor="cash">Cash available</label>
            <div className="money-input">
              <span>$</span>
              <input
                id="cash"
                min="100"
                step="100"
                type="number"
                value={initialCapital}
                onChange={(event) => {
                  const value = Number(event.target.value);
                  setInitialCapital(Number.isFinite(value) && value > 0 ? value : DEFAULT_INITIAL_CAPITAL);
                }}
              />
            </div>
          </div>
          <div className="field">
            <label htmlFor="symbol">Symbol</label>
            <select id="symbol" value={symbol} onChange={(event) => setSymbol(event.target.value)}>
              {SYMBOLS.map((candidate) => (
                <option key={candidate} value={candidate}>
                  {candidate}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {error ? <section className="alert">{error}</section> : null}

      <section className="metrics-grid" aria-busy={loading}>
        <MetricTile label="Equity" value={result ? dollars(result.portfolio.equity) : "..."} tone={tone} />
        <MetricTile label="Net P&L" value={result ? dollars(result.performance.netProfit) : "..."} tone={tone} />
        <MetricTile label="Win Rate" value={result ? `${result.performance.winRate.toFixed(1)}%` : "..."} />
        <MetricTile
          label="Profit Factor"
          value={result?.performance.profitFactor ? result.performance.profitFactor.toFixed(2) : "n/a"}
        />
        <MetricTile label="Trades" value={result ? String(result.performance.trades) : "..."} />
        <MetricTile
          label="Return"
          value={result ? `${result.portfolio.totalReturnPct.toFixed(2)}%` : "..."}
          tone={tone}
        />
      </section>

      {result ? (
        <div className="workspace-grid">
          <ScannerTable signals={result.signals} />
          <TradeJournal trades={result.trades} />
        </div>
      ) : (
        <section className="panel loading-panel">Loading simulation...</section>
      )}
    </main>
  );
}
