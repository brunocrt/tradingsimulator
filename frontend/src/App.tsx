import { useEffect, useMemo, useState } from "react";
import { MetricTile } from "./components/MetricTile";
import { ScannerTable } from "./components/ScannerTable";
import { TradeChart } from "./components/TradeChart";
import { TradeJournal } from "./components/TradeJournal";
import { runBacktest } from "./lib/api";
import { sampleResult } from "./lib/sampleResult";
import type { BacktestRequest, BacktestResult } from "./lib/types";
import "./styles.css";

const SYMBOLS = ["AMD", "NVDA", "AAPL", "MSFT", "TSLA", "SPY"];
const DEFAULT_INITIAL_CAPITAL = 1000;
const PROVIDERS = [
  { label: "Yahoo Finance", value: "yahoo" },
  { label: "Polygon", value: "polygon" },
  { label: "Sample", value: "sample" }
];
const TIMEFRAMES = [
  { label: "1 day", value: "1d" },
  { label: "1 hour", value: "1h" },
  { label: "15 min", value: "15m" },
  { label: "5 min", value: "5m" },
  { label: "1 min", value: "1m" }
];

const DEFAULT_BACKTEST_REQUEST: BacktestRequest = {
  symbol: "AMD",
  initialCapital: DEFAULT_INITIAL_CAPITAL,
  provider: "yahoo",
  start: "2024-01-01",
  end: "2024-06-30",
  timeframe: "1d"
};

function dollars(value: number) {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export default function App() {
  const [symbol, setSymbol] = useState(DEFAULT_BACKTEST_REQUEST.symbol);
  const [initialCapital, setInitialCapital] = useState(DEFAULT_BACKTEST_REQUEST.initialCapital);
  const [provider, setProvider] = useState(DEFAULT_BACKTEST_REQUEST.provider);
  const [apiKey, setApiKey] = useState("");
  const [timeframe, setTimeframe] = useState(DEFAULT_BACKTEST_REQUEST.timeframe);
  const [startDate, setStartDate] = useState(DEFAULT_BACKTEST_REQUEST.start);
  const [endDate, setEndDate] = useState(DEFAULT_BACKTEST_REQUEST.end);
  const [runRequest, setRunRequest] = useState<BacktestRequest>(DEFAULT_BACKTEST_REQUEST);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [selectedTradeIndex, setSelectedTradeIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    runBacktest(runRequest)
      .then((nextResult) => {
        setResult(nextResult);
        setSelectedTradeIndex(0);
      })
      .catch((err: unknown) => {
        setResult(sampleResult);
        setSelectedTradeIndex(0);
        console.info("Using bundled sample backtest because the API is unavailable.", err);
      })
      .finally(() => setLoading(false));
  }, [runRequest]);

  function submitBacktest() {
    setRunRequest({
      symbol,
      initialCapital,
      provider,
      start: startDate,
      end: endDate,
      timeframe,
      apiKey: provider === "polygon" ? apiKey : undefined
    });
  }

  const tone = useMemo(() => {
    if (!result) return "neutral";
    return result.portfolio.realizedPnl >= 0 ? "good" : "bad";
  }, [result]);

  const selectedTrade = result?.trades[selectedTradeIndex] ?? null;

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
            <label htmlFor="provider">Data</label>
            <select id="provider" value={provider} onChange={(event) => setProvider(event.target.value)}>
              {PROVIDERS.map((candidate) => (
                <option key={candidate.value} value={candidate.value}>
                  {candidate.label}
                </option>
              ))}
            </select>
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
          <div className="field">
            <label htmlFor="timeframe">Timeframe</label>
            <select id="timeframe" value={timeframe} onChange={(event) => setTimeframe(event.target.value)}>
              {TIMEFRAMES.map((candidate) => (
                <option key={candidate.value} value={candidate.value}>
                  {candidate.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="startDate">Start</label>
            <input id="startDate" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="endDate">End</label>
            <input id="endDate" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </div>
          {provider === "polygon" ? (
            <div className="field api-key-field">
              <label htmlFor="apiKey">API key</label>
              <input
                id="apiKey"
                placeholder="Polygon API key"
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
              />
            </div>
          ) : null}
          <button className="run-button" disabled={loading} type="button" onClick={submitBacktest}>
            {loading ? "Running" : "Run Backtest"}
          </button>
        </div>
      </header>

      {error ? <section className="alert">{error}</section> : null}
      {result?.dataSource ? (
        <section className={result.dataSource.warning ? "data-source data-source-warning" : "data-source"}>
          <strong>{result.dataSource.source}</strong>
          <span>
            {result.dataSource.symbol} | {result.dataSource.timeframe} | {result.dataSource.candles} candles |{" "}
            {result.dataSource.start} to {result.dataSource.end}
          </span>
          {result.dataSource.warning ? <em>{result.dataSource.warning}</em> : null}
        </section>
      ) : null}

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
        <>
          <div className="chart-grid">
            <TradeChart candles={result.candles} selectedTrade={selectedTrade} trades={result.trades} />
          </div>
          <div className="workspace-grid">
            <ScannerTable signals={result.signals} />
            <TradeJournal
              trades={result.trades}
              selectedTrade={selectedTrade}
              onSelectTrade={(trade) => setSelectedTradeIndex(result.trades.indexOf(trade))}
            />
          </div>
        </>
      ) : (
        <section className="panel loading-panel">Loading simulation...</section>
      )}
    </main>
  );
}
