from dataclasses import replace
from datetime import date

from fastapi import APIRouter, Query

from app.core.config import SimulatorConfig
from app.services.backtest import run_single_symbol_backtest
from app.services.market_data import MarketDataProviderName, MarketDataRequest, fetch_market_data
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
    provider: MarketDataProviderName = Query(default=MarketDataProviderName.YAHOO),
    start: date = Query(default=date(2024, 1, 1)),
    end: date = Query(default=date(2024, 6, 30)),
    timeframe: str = Query(default="1d", pattern="^(1m|5m|15m|1h|1d)$"),
    api_key: str | None = Query(default=None, alias="apiKey"),
) -> dict:
    config = replace(CONFIG, initial_capital=initial_capital)
    market_data = fetch_market_data(
        MarketDataRequest(
            symbol=symbol.upper(),
            provider=provider,
            start=start,
            end=end,
            timeframe=timeframe,
            api_key=api_key,
        )
    )
    result = run_single_symbol_backtest(
        market_data.candles,
        average_volume=sample_average_volume(),
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=config,
    )
    result["dataSource"] = {
        "provider": market_data.provider,
        "source": market_data.source,
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "candles": len(market_data.candles),
        "warning": market_data.warning,
    }
    return result


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
