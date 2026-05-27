# Architecture

The MVP is split into three layers.

## Simulation Core

The backend core is deterministic. It calculates indicators, liquidity scores, strategy signals, risk decisions, simulated fills, and journal entries without LLM involvement. This keeps backtests reproducible and avoids delegating approval decisions to non-deterministic agents.

## API

FastAPI exposes the initial REST contract from the specification:

- `/api/config`
- `/api/watchlists`
- `/api/market/status`
- `/api/market/candles/{symbol}`
- `/api/signals`
- `/api/signals/scan`
- `/api/opportunities/scan`
- `/api/simulation/backtest`
- `/api/simulation/status`
- `/api/portfolio`
- `/api/portfolio/performance`
- `/api/trades/journal`

Market data flows through a provider interface with implementations for generated sample candles, Yahoo Finance historical candles, and Polygon aggregates. Backtests, candle reads, and signal scans all use the same provider request path so API behavior stays consistent across research views.

The opportunity scanner runs a symbol universe through the same deterministic signal engine, adds momentum and liquidity scoring, and returns a ranked shortlist. It supports three universe modes: cached exchange ticker master, built-in liquid discovery universe, and custom comma-separated symbols. The ticker master is refreshed from Nasdaq Trader symbol directory files and cached locally. This separates opportunity discovery from the single-symbol backtest flow and prepares the simulator for portfolio-level allocation.

Exchange-wide NYSE/Nasdaq screening still needs persisted historical candle caching and rate-limit aware refresh jobs before thousands of symbols can be scanned cheaply and reliably on every request.

## Dashboard

The React dashboard is an operational screen, not a marketing page. It shows account metrics, signal decisions, risk context, and closed trade journal entries.

## Safety Defaults

- Live trading is disabled.
- Trades require stop-loss levels.
- Position size is derived from equity and configured risk.
- Backtest P&L includes spread, slippage, and regulatory fee assumptions.
- Rejected trade reasons are preserved for auditability.
