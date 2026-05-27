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
- `/api/simulation/backtest`
- `/api/simulation/status`
- `/api/portfolio`
- `/api/portfolio/performance`
- `/api/trades/journal`

The API currently uses generated sample candles. The next backend step is to introduce a `MarketDataProvider` interface for historical and delayed market data providers.

## Dashboard

The React dashboard is an operational screen, not a marketing page. It shows account metrics, signal decisions, risk context, and closed trade journal entries.

## Safety Defaults

- Live trading is disabled.
- Trades require stop-loss levels.
- Position size is derived from equity and configured risk.
- Backtest P&L includes spread, slippage, and regulatory fee assumptions.
- Rejected trade reasons are preserved for auditability.

