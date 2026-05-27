from dataclasses import replace

from fastapi import APIRouter, Query

from app.core.config import SimulatorConfig
from app.services.backtest import run_single_symbol_backtest
from app.services.orchestrator import scan_symbol
from app.services.sample_data import generate_intraday_candles, sample_average_volume

router = APIRouter(prefix="/api")

CONFIG = SimulatorConfig()


@router.get("/config")
def get_config() -> dict:
    return {
        "initialCapital": CONFIG.initial_capital,
        "riskPerTradePct": CONFIG.risk_per_trade_pct,
        "maxDailyLossPct": CONFIG.max_daily_loss_pct,
        "maxOpenPositions": CONFIG.max_open_positions,
        "maxTradesPerDay": CONFIG.max_trades_per_day,
        "allowedStrategies": list(CONFIG.enabled_strategies),
        "watchlist": CONFIG.watchlist,
    }


@router.get("/watchlists")
def get_watchlists() -> list[dict]:
    return [{"id": "default-liquid-us", "name": "Liquid US MVP", "symbols": CONFIG.watchlist}]


@router.get("/market/status")
def market_status() -> dict:
    return {
        "market": "US_EQUITIES",
        "mode": "simulation",
        "liveTradingEnabled": False,
        "dataFeed": "sample",
        "status": "DELAYED_OR_SIMULATED",
    }


@router.get("/market/candles/{symbol}")
def candles(symbol: str) -> list[dict]:
    return [candle.__dict__ for candle in generate_intraday_candles(symbol.upper())]


@router.get("/signals")
def latest_signals(symbol: str = "AMD") -> list[dict]:
    candles_for_symbol = generate_intraday_candles(symbol.upper())
    signals = scan_symbol(
        candles_for_symbol,
        average_volume=sample_average_volume(),
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=CONFIG,
    )
    return [signal.to_dict() for signal in signals]


@router.post("/signals/scan")
def scan(symbol: str = "AMD") -> dict:
    return {"signals": latest_signals(symbol)}


@router.post("/simulation/backtest")
def backtest(
    symbol: str = "AMD",
    initial_capital: float = Query(default=1000.0, alias="initialCapital", ge=100.0, le=10_000_000.0),
) -> dict:
    config = replace(CONFIG, initial_capital=initial_capital)
    return run_single_symbol_backtest(
        generate_intraday_candles(symbol.upper()),
        average_volume=sample_average_volume(),
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=config,
    )


@router.get("/simulation/status")
def simulation_status() -> dict:
    return {"mode": "backtest", "paperTrading": "stopped", "liveTrading": "disabled"}


@router.get("/portfolio")
def portfolio() -> dict:
    return backtest()["portfolio"]


@router.get("/portfolio/performance")
def performance() -> dict:
    return backtest()["performance"]


@router.get("/trades/journal")
def journal() -> list[dict]:
    return backtest()["trades"]
