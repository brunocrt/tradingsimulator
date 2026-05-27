from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import csv
import os
from pathlib import Path
from urllib.request import Request, urlopen

from app.core.config import DEFAULT_DISCOVERY_UNIVERSE


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
DEFAULT_TICKER_MASTER_PATH = Path(os.environ.get("TICKER_MASTER_PATH", "/tmp/trading-simulator/ticker_master.csv"))


@dataclass(frozen=True)
class Ticker:
    symbol: str
    name: str
    exchange: str
    is_etf: bool
    source: str
    refreshed_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def refresh_ticker_master(path: Path = DEFAULT_TICKER_MASTER_PATH) -> list[Ticker]:
    refreshed_at = datetime.now(timezone.utc).isoformat()
    tickers = _parse_nasdaq_listed(_download_text(NASDAQ_LISTED_URL), refreshed_at)
    tickers.extend(_parse_other_listed(_download_text(OTHER_LISTED_URL), refreshed_at))
    unique = _dedupe_and_sort(tickers)
    _write_tickers(unique, path)
    return unique


def load_ticker_master(path: Path = DEFAULT_TICKER_MASTER_PATH) -> list[Ticker]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [
            Ticker(
                symbol=row["symbol"],
                name=row["name"],
                exchange=row["exchange"],
                is_etf=row["is_etf"].lower() == "true",
                source=row["source"],
                refreshed_at=row["refreshed_at"],
            )
            for row in csv.DictReader(handle)
        ]


def ticker_master_status(path: Path = DEFAULT_TICKER_MASTER_PATH) -> dict:
    tickers = load_ticker_master(path)
    refreshed_at = tickers[0].refreshed_at if tickers else None
    exchanges: dict[str, int] = {}
    for ticker in tickers:
        exchanges[ticker.exchange] = exchanges.get(ticker.exchange, 0) + 1
    return {
        "path": str(path),
        "cached": bool(tickers),
        "symbols": len(tickers),
        "refreshedAt": refreshed_at,
        "exchanges": exchanges,
    }


def exchange_universe_symbols(
    include_etfs: bool = False,
    max_symbols: int | None = None,
    path: Path = DEFAULT_TICKER_MASTER_PATH,
) -> list[str]:
    tickers = load_ticker_master(path)
    if not tickers:
        symbols = DEFAULT_DISCOVERY_UNIVERSE.copy()
    else:
        cached_symbols = [ticker.symbol for ticker in tickers if include_etfs or not ticker.is_etf]
        discovery_first = [symbol for symbol in DEFAULT_DISCOVERY_UNIVERSE if symbol in cached_symbols]
        remaining = [symbol for symbol in cached_symbols if symbol not in set(discovery_first)]
        symbols = discovery_first + remaining
    return symbols[:max_symbols] if max_symbols else symbols


def _download_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "trading-simulator/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def _parse_nasdaq_listed(payload: str, refreshed_at: str) -> list[Ticker]:
    rows = _pipe_rows(payload)
    tickers: list[Ticker] = []
    for row in rows:
        symbol = row.get("Symbol", "")
        if not _is_tradeable_symbol(symbol) or row.get("Test Issue") != "N":
            continue
        tickers.append(
            Ticker(
                symbol=_normalize_symbol(symbol),
                name=row.get("Security Name", ""),
                exchange="NASDAQ",
                is_etf=row.get("ETF") == "Y",
                source="nasdaqlisted.txt",
                refreshed_at=refreshed_at,
            )
        )
    return tickers


def _parse_other_listed(payload: str, refreshed_at: str) -> list[Ticker]:
    rows = _pipe_rows(payload)
    tickers: list[Ticker] = []
    for row in rows:
        symbol = row.get("ACT Symbol", "")
        exchange = _exchange_name(row.get("Exchange", ""))
        if exchange not in {"NYSE", "NYSE_AMERICAN"}:
            continue
        if not _is_tradeable_symbol(symbol) or row.get("Test Issue") != "N":
            continue
        tickers.append(
            Ticker(
                symbol=_normalize_symbol(symbol),
                name=row.get("Security Name", ""),
                exchange=exchange,
                is_etf=row.get("ETF") == "Y",
                source="otherlisted.txt",
                refreshed_at=refreshed_at,
            )
        )
    return tickers


def _pipe_rows(payload: str) -> list[dict[str, str]]:
    lines = [line for line in payload.splitlines() if line and not line.startswith("File Creation Time")]
    reader = csv.DictReader(lines, delimiter="|")
    return [row for row in reader if row]


def _dedupe_and_sort(tickers: list[Ticker]) -> list[Ticker]:
    by_symbol: dict[str, Ticker] = {}
    for ticker in tickers:
        by_symbol.setdefault(ticker.symbol, ticker)
    return [by_symbol[symbol] for symbol in sorted(by_symbol)]


def _write_tickers(tickers: list[Ticker], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "name", "exchange", "is_etf", "source", "refreshed_at"])
        writer.writeheader()
        for ticker in tickers:
            writer.writerow(ticker.to_dict())


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace("/", "-")


def _is_tradeable_symbol(symbol: str) -> bool:
    normalized = _normalize_symbol(symbol)
    return bool(normalized) and "$" not in normalized and "." not in normalized


def _exchange_name(code: str) -> str:
    return {
        "A": "NYSE_AMERICAN",
        "N": "NYSE",
    }.get(code, code)
