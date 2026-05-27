from app.api.routes import DEFAULT_END, DEFAULT_START, candles, latest_signals, opportunities_scan, portfolio
from app.services.market_data import MarketDataProviderName


def test_market_candles_route_uses_requested_provider_defaults() -> None:
    payload = candles(
        "AMD",
        provider=MarketDataProviderName.SAMPLE,
        start=DEFAULT_START,
        end=DEFAULT_END,
        timeframe="1d",
        api_key=None,
    )
    assert payload["dataSource"]["provider"] == "sample"
    assert payload["dataSource"]["source"] == "generated sample candles"
    assert payload["candles"]
    assert payload["candles"][0]["symbol"] == "AMD"


def test_signals_route_includes_data_source_metadata() -> None:
    payload = latest_signals(
        "AMD",
        provider=MarketDataProviderName.SAMPLE,
        start=DEFAULT_START,
        end=DEFAULT_END,
        timeframe="1d",
        api_key=None,
    )
    assert payload["dataSource"]["provider"] == "sample"
    assert payload["signals"]


def test_portfolio_route_uses_internal_backtest_defaults() -> None:
    payload = portfolio()
    assert payload["initialCapital"] == 1000.0
    assert payload["cash"] >= 0


def test_opportunities_scan_route_returns_ranked_candidates() -> None:
    payload = opportunities_scan(
        symbols="AMD,AAPL,MSFT",
        provider=MarketDataProviderName.SAMPLE,
        start=DEFAULT_START,
        end=DEFAULT_END,
        timeframe="1d",
        limit=2,
        api_key=None,
    )

    assert payload["universeSize"] == 3
    assert len(payload["opportunities"]) == 2
    assert payload["opportunities"][0]["rank"] == 1


def test_opportunities_scan_defaults_to_discovery_universe() -> None:
    payload = opportunities_scan(
        symbols=None,
        provider=MarketDataProviderName.SAMPLE,
        start=DEFAULT_START,
        end=DEFAULT_END,
        timeframe="1d",
        limit=25,
        api_key=None,
    )

    assert payload["universeSize"] > 50
    assert len(payload["opportunities"]) == 25
