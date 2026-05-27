from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from enum import StrEnum
import json
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.models.domain import Candle
from app.services.sample_data import generate_intraday_candles


class MarketDataProviderName(StrEnum):
    SAMPLE = "sample"
    YAHOO = "yahoo"
    POLYGON = "polygon"


@dataclass(frozen=True)
class MarketDataRequest:
    symbol: str
    provider: MarketDataProviderName
    start: date
    end: date
    timeframe: str
    api_key: str | None = None


@dataclass(frozen=True)
class MarketDataResult:
    candles: list[Candle]
    provider: str
    source: str
    warning: str | None = None


class MarketDataProvider(Protocol):
    name: MarketDataProviderName
    source: str

    def fetch(self, request: MarketDataRequest) -> list[Candle]:
        ...


TIMEFRAME_TO_YAHOO_INTERVAL = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "1d": "1d",
}

TIMEFRAME_TO_POLYGON = {
    "1m": (1, "minute"),
    "5m": (5, "minute"),
    "15m": (15, "minute"),
    "1h": (1, "hour"),
    "1d": (1, "day"),
}


class SampleMarketDataProvider:
    name = MarketDataProviderName.SAMPLE
    source = "generated sample candles"

    def fetch(self, request: MarketDataRequest) -> list[Candle]:
        return generate_intraday_candles(request.symbol)


class YahooMarketDataProvider:
    name = MarketDataProviderName.YAHOO
    source = "Yahoo Finance chart API"

    def fetch(self, request: MarketDataRequest) -> list[Candle]:
        interval = TIMEFRAME_TO_YAHOO_INTERVAL.get(request.timeframe)
        if interval is None:
            raise ValueError(f"Unsupported Yahoo timeframe: {request.timeframe}")
        period1 = _unix_start(request.start)
        period2 = _unix_end(request.end)
        params = urlencode({"period1": period1, "period2": period2, "interval": interval, "includePrePost": "false"})
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{request.symbol.upper()}?{params}"
        payload = _get_json(url)
        chart = payload.get("chart", {})
        if chart.get("error"):
            raise ValueError(chart["error"].get("description", "Yahoo chart error"))
        result = (chart.get("result") or [None])[0]
        if not result:
            raise ValueError("Yahoo returned no chart data")
        timestamps = result.get("timestamp") or []
        quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        candles = _candles_from_arrays(
            symbol=request.symbol,
            timeframe=request.timeframe,
            timestamps=timestamps,
            opens=quote.get("open") or [],
            highs=quote.get("high") or [],
            lows=quote.get("low") or [],
            closes=quote.get("close") or [],
            volumes=quote.get("volume") or [],
        )
        if len(candles) < 60:
            raise ValueError("Yahoo returned too few candles for the strategy warmup")
        return candles


class PolygonMarketDataProvider:
    name = MarketDataProviderName.POLYGON
    source = "Polygon aggregates API"

    def fetch(self, request: MarketDataRequest) -> list[Candle]:
        if not request.api_key:
            raise ValueError("Polygon requires an API key")
        multiplier, timespan = TIMEFRAME_TO_POLYGON.get(request.timeframe, (0, ""))
        if not multiplier:
            raise ValueError(f"Unsupported Polygon timeframe: {request.timeframe}")
        params = urlencode({"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": request.api_key})
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{request.symbol.upper()}/range/"
            f"{multiplier}/{timespan}/{request.start.isoformat()}/{request.end.isoformat()}?{params}"
        )
        payload = _get_json(url)
        if payload.get("status") not in {"OK", "DELAYED"}:
            raise ValueError(payload.get("error") or payload.get("message") or "Polygon request failed")
        candles = [
            Candle(
                symbol=request.symbol.upper(),
                timestamp=datetime.fromtimestamp(item["t"] / 1000, tz=timezone.utc).replace(tzinfo=None),
                open=round(float(item["o"]), 4),
                high=round(float(item["h"]), 4),
                low=round(float(item["l"]), 4),
                close=round(float(item["c"]), 4),
                volume=int(item.get("v") or 0),
                timeframe=request.timeframe,
            )
            for item in payload.get("results", [])
        ]
        if len(candles) < 60:
            raise ValueError("Polygon returned too few candles for the strategy warmup")
        return candles


PROVIDERS: dict[MarketDataProviderName, MarketDataProvider] = {
    MarketDataProviderName.SAMPLE: SampleMarketDataProvider(),
    MarketDataProviderName.YAHOO: YahooMarketDataProvider(),
    MarketDataProviderName.POLYGON: PolygonMarketDataProvider(),
}


def fetch_market_data(request: MarketDataRequest) -> MarketDataResult:
    provider = PROVIDERS.get(request.provider)
    if provider is None:
        return _sample_result(request)

    try:
        candles = provider.fetch(request)
        return MarketDataResult(candles=candles, provider=provider.name.value, source=provider.source)
    except Exception as exc:
        fallback = _sample_result(request)
        return MarketDataResult(
            candles=fallback.candles,
            provider=request.provider.value,
            source="sample fallback",
            warning=f"{request.provider.value} data unavailable: {exc}",
        )


def average_volume(candles: list[Candle]) -> int:
    if not candles:
        return 0
    return round(sum(candle.volume for candle in candles) / len(candles))


def _sample_result(request: MarketDataRequest) -> MarketDataResult:
    provider = PROVIDERS[MarketDataProviderName.SAMPLE]
    return MarketDataResult(
        candles=provider.fetch(request),
        provider=provider.name.value,
        source=provider.source,
    )


def _get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "trading-simulator/0.1"})
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _candles_from_arrays(
    symbol: str,
    timeframe: str,
    timestamps: list[int],
    opens: list[float | None],
    highs: list[float | None],
    lows: list[float | None],
    closes: list[float | None],
    volumes: list[int | None],
) -> list[Candle]:
    candles: list[Candle] = []
    for index, timestamp in enumerate(timestamps):
        values = [opens, highs, lows, closes, volumes]
        if any(index >= len(series) or series[index] is None for series in values):
            continue
        candles.append(
            Candle(
                symbol=symbol.upper(),
                timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None),
                open=round(float(opens[index]), 4),
                high=round(float(highs[index]), 4),
                low=round(float(lows[index]), 4),
                close=round(float(closes[index]), 4),
                volume=int(volumes[index] or 0),
                timeframe=timeframe,
            )
        )
    return candles


def _unix_start(value: date) -> int:
    return int(datetime.combine(value, time.min, tzinfo=timezone.utc).timestamp())


def _unix_end(value: date) -> int:
    return int(datetime.combine(value, time.max, tzinfo=timezone.utc).timestamp())
