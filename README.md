# Autonomous Multi-Agent Stock Trading Simulator

Risk-first stock trading simulation workspace for research, backtesting, and future paper trading. Live trading is intentionally disabled.

## What is implemented

- Deterministic Python simulation core.
- FastAPI endpoints for config, watchlist, market status, signals, backtest results, portfolio, and trade journal.
- Rule-based MVP strategies:
  - VWAP pullback
  - Opening range breakout
  - Trend continuation
- Anti-chase checks through crowding, trap-risk, and entry-quality scoring.
- Risk-based position sizing from account equity.
- Cost-aware simulated fills using spread, slippage, commissions, SEC fee, and FINRA fee assumptions.
- React dashboard for portfolio metrics, scanner decisions, and trade journal.
- Sample intraday candles so the app runs without market-data provider credentials.

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

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

## Next Build Steps

1. Replace sample candles with a `MarketDataProvider` interface implementation.
2. Persist candles, signals, orders, positions, and journal entries in PostgreSQL.
3. Add WebSocket updates for paper-trading mode.
4. Expand backtest metrics with drawdown, Sharpe, Sortino, expectancy, and slippage impact.
5. Add structured agent reasoning logs while keeping trade approval deterministic.
