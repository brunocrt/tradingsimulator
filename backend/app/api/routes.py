from dataclasses import replace
from datetime import date

from fastapi import APIRouter, Query

from app.core.config import SimulatorConfig
from app.services.backtest import run_single_symbol_backtest
from app.services.market_data import MarketDataProviderName, MarketDataRequest, average_volume, fetch_market_data
from app.services.opportunities import scan_opportunities
from app.services.orchestrator import scan_symbol
from app.services.ticker_master import exchange_universe_symbols, refresh_ticker_master, ticker_master_status

router = APIRouter(prefix="/api")

CONFIG = SimulatorConfig()

DEFAULT_SYMBOL = "AMD"
DEFAULT_START = date(2024, 1, 1)
DEFAULT_END = date(2024, 6, 30)
TIMEFRAME_PATTERN = "^(1m|5m|15m|1h|1d)$"


def _market_data_request(
    symbol: str,
    provider: MarketDataProviderName,
    start: date,
    end: date,
    timeframe: str,
    api_key: str | None,
) -> MarketDataRequest:
    return MarketDataRequest(
        symbol=symbol.upper(),
        provider=provider,
        start=start,
        end=end,
        timeframe=timeframe,
        api_key=api_key,
    )


def _data_source(
    market_data,
    symbol: str,
    timeframe: str,
    start: date,
    end: date,
) -> dict:
    return {
        "provider": market_data.provider,
        "source": market_data.source,
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "candles": len(market_data.candles),
        "warning": market_data.warning,
    }


def _run_backtest(
    symbol: str,
    initial_capital: float,
    provider: MarketDataProviderName,
    start: date,
    end: date,
    timeframe: str,
    api_key: str | None,
) -> dict:
    config = replace(CONFIG, initial_capital=initial_capital)
    market_data = fetch_market_data(_market_data_request(symbol, provider, start, end, timeframe, api_key))
    result = run_single_symbol_backtest(
        market_data.candles,
        average_volume=average_volume(market_data.candles),
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=config,
    )
    result["dataSource"] = _data_source(market_data, symbol, timeframe, start, end)
    return result


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
        "discoveryUniverseSize": len(CONFIG.discovery_universe),
    }


@router.get("/watchlists")
def get_watchlists() -> list[dict]:
    return [
        {"id": "default-liquid-us", "name": "Liquid US MVP", "symbols": CONFIG.watchlist},
        {"id": "discovery-liquid-us", "name": "Liquid US Discovery", "symbols": CONFIG.discovery_universe},
    ]


@router.get("/universe/status")
def universe_status() -> dict:
    return ticker_master_status()


@router.post("/universe/refresh")
def universe_refresh() -> dict:
    tickers = refresh_ticker_master()
    status = ticker_master_status()
    return {**status, "symbols": len(tickers)}


@router.get("/market/status")
def market_status() -> dict:
    return {
        "market": "US_EQUITIES",
        "mode": "simulation",
        "liveTradingEnabled": False,
        "dataFeed": MarketDataProviderName.YAHOO.value,
        "availableDataFeeds": [provider.value for provider in MarketDataProviderName],
        "status": "DELAYED_OR_SIMULATED",
    }


@router.get("/market/candles/{symbol}")
def candles(
    symbol: str,
    provider: MarketDataProviderName = Query(default=MarketDataProviderName.YAHOO),
    start: date = Query(default=DEFAULT_START),
    end: date = Query(default=DEFAULT_END),
    timeframe: str = Query(default="1d", pattern=TIMEFRAME_PATTERN),
    api_key: str | None = Query(default=None, alias="apiKey"),
) -> dict:
    market_data = fetch_market_data(_market_data_request(symbol, provider, start, end, timeframe, api_key))
    return {
        "dataSource": _data_source(market_data, symbol, timeframe, start, end),
        "candles": [candle.__dict__ for candle in market_data.candles],
    }


@router.get("/signals")
def latest_signals(
    symbol: str = DEFAULT_SYMBOL,
    provider: MarketDataProviderName = Query(default=MarketDataProviderName.YAHOO),
    start: date = Query(default=DEFAULT_START),
    end: date = Query(default=DEFAULT_END),
    timeframe: str = Query(default="1d", pattern=TIMEFRAME_PATTERN),
    api_key: str | None = Query(default=None, alias="apiKey"),
) -> dict:
    market_data = fetch_market_data(_market_data_request(symbol, provider, start, end, timeframe, api_key))
    signals = scan_symbol(
        market_data.candles,
        average_volume=average_volume(market_data.candles),
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=CONFIG,
    )
    return {
        "dataSource": _data_source(market_data, symbol, timeframe, start, end),
        "signals": [signal.to_dict() for signal in signals],
    }


@router.post("/signals/scan")
def scan(
    symbol: str = DEFAULT_SYMBOL,
    provider: MarketDataProviderName = Query(default=MarketDataProviderName.YAHOO),
    start: date = Query(default=DEFAULT_START),
    end: date = Query(default=DEFAULT_END),
    timeframe: str = Query(default="1d", pattern=TIMEFRAME_PATTERN),
    api_key: str | None = Query(default=None, alias="apiKey"),
) -> dict:
    return latest_signals(symbol, provider, start, end, timeframe, api_key)


@router.get("/opportunities/scan")
def opportunities_scan(
    universe: str = Query(default="exchange", pattern="^(exchange|discovery|custom)$"),
    symbols: str | None = Query(
        default=None,
        description="Comma-separated symbols. Used when universe=custom.",
    ),
    include_etfs: bool = Query(default=False, alias="includeEtfs"),
    max_symbols: int = Query(default=250, alias="maxSymbols", ge=1, le=10000),
    provider: MarketDataProviderName = Query(default=MarketDataProviderName.YAHOO),
    start: date = Query(default=DEFAULT_START),
    end: date = Query(default=DEFAULT_END),
    timeframe: str = Query(default="1d", pattern=TIMEFRAME_PATTERN),
    limit: int = Query(default=25, ge=1, le=250),
    api_key: str | None = Query(default=None, alias="apiKey"),
) -> dict:
    universe_symbols = _opportunity_universe(universe, symbols, include_etfs, max_symbols)
    opportunities = scan_opportunities(
        symbols=universe_symbols,
        provider=provider,
        start=start,
        end=end,
        timeframe=timeframe,
        api_key=api_key,
        config=CONFIG,
        limit=limit,
    )
    return {
        "universe": universe,
        "universeSize": len(universe_symbols),
        "provider": provider.value,
        "timeframe": timeframe,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "opportunities": [opportunity.to_dict() for opportunity in opportunities],
    }


@router.post("/simulation/backtest")
def backtest(
    symbol: str = "AMD",
    initial_capital: float = Query(default=1000.0, alias="initialCapital", ge=100.0, le=10_000_000.0),
    provider: MarketDataProviderName = Query(default=MarketDataProviderName.YAHOO),
    start: date = Query(default=DEFAULT_START),
    end: date = Query(default=DEFAULT_END),
    timeframe: str = Query(default="1d", pattern=TIMEFRAME_PATTERN),
    api_key: str | None = Query(default=None, alias="apiKey"),
) -> dict:
    return _run_backtest(symbol, initial_capital, provider, start, end, timeframe, api_key)


@router.get("/simulation/status")
def simulation_status() -> dict:
    return {"mode": "backtest", "paperTrading": "stopped", "liveTrading": "disabled"}


@router.get("/portfolio")
def portfolio() -> dict:
    return _run_backtest(DEFAULT_SYMBOL, 1000.0, MarketDataProviderName.YAHOO, DEFAULT_START, DEFAULT_END, "1d", None)[
        "portfolio"
    ]


@router.get("/portfolio/performance")
def performance() -> dict:
    return _run_backtest(DEFAULT_SYMBOL, 1000.0, MarketDataProviderName.YAHOO, DEFAULT_START, DEFAULT_END, "1d", None)[
        "performance"
    ]


@router.get("/trades/journal")
def journal() -> list[dict]:
    return _run_backtest(DEFAULT_SYMBOL, 1000.0, MarketDataProviderName.YAHOO, DEFAULT_START, DEFAULT_END, "1d", None)[
        "trades"
    ]


def _parse_symbols(symbols: str) -> list[str]:
    parsed = [symbol.strip().upper() for symbol in symbols.split(",")]
    return [symbol for symbol in parsed if symbol]


def _opportunity_universe(
    universe: str,
    symbols: str | None,
    include_etfs: bool,
    max_symbols: int,
) -> list[str]:
    if universe == "custom":
        return _parse_symbols(symbols or "")
    if universe == "discovery":
        return CONFIG.discovery_universe[:max_symbols]
    return exchange_universe_symbols(include_etfs=include_etfs, max_symbols=max_symbols)
