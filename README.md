# Autonomous Multi-Agent Stock Trading Simulator

Risk-first stock trading simulation workspace for research, backtesting, and future paper trading. Live trading is intentionally disabled.

## What is implemented

- Deterministic Python simulation core.
- FastAPI endpoints for config, watchlist, market status, signals, backtest results, portfolio, and trade journal.
- Ranked opportunity scanner across the configured watchlist.
- Rule-based MVP strategies:
  - VWAP pullback
  - Opening range breakout
  - Trend continuation
- Anti-chase checks through crowding, trap-risk, and entry-quality scoring.
- Risk-based position sizing from account equity.
- Cost-aware simulated fills using spread, slippage, commissions, SEC fee, and FINRA fee assumptions.
- React dashboard for portfolio metrics, scanner decisions, and trade journal.
- Yahoo Finance historical candles by default, with sample fallback.
- Polygon historical aggregates as an API-key configurable provider.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The dashboard runs at [http://127.0.0.1:5173](http://127.0.0.1:5173).

## Docker Compose

```powershell
docker compose up --build
```

If Docker Desktop is not running but Podman is available:

```powershell
podman compose up --build -d
```

Then open:

- Dashboard: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

The frontend container is built with `VITE_API_BASE=http://127.0.0.1:8000`, so the browser talks to the API through the published backend port.

## Market Data

The dashboard supports:

- `Yahoo Finance`: default free historical data provider.
- `Polygon`: configurable provider that requires an API key in the UI.
- `Sample`: generated candles for offline development and demos.

Backtest, candle, signal, and opportunity scan requests accept `provider`, `start`, `end`, `timeframe`, and optional `apiKey`. Backtests also accept `symbol` and `initialCapital`; opportunity scans can optionally accept comma-separated `symbols`.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

## Next Build Steps

1. Add multi-symbol portfolio backtesting that allocates capital from ranked opportunities.
2. Add adaptive exits with trailing stops, partial profits, and momentum continuation checks.
3. Persist candles, signals, orders, positions, and journal entries in PostgreSQL.
4. Add WebSocket updates for paper-trading mode.
5. Expand backtest metrics with drawdown, Sharpe, Sortino, expectancy, and slippage impact.
6. Add structured agent reasoning logs while keeping trade approval deterministic.
