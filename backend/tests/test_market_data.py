from datetime import date

from app.services.market_data import MarketDataProviderName, MarketDataRequest, fetch_market_data


def test_sample_market_data_provider_returns_candles() -> None:
    result = fetch_market_data(
        MarketDataRequest(
            symbol="AMD",
            provider=MarketDataProviderName.SAMPLE,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            timeframe="1d",
        )
    )

    assert result.provider == "sample"
    assert result.candles
    assert result.candles[0].symbol == "AMD"


def test_polygon_without_key_falls_back_to_sample_with_warning() -> None:
    result = fetch_market_data(
        MarketDataRequest(
            symbol="AMD",
            provider=MarketDataProviderName.POLYGON,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            timeframe="1d",
        )
    )

    assert result.source == "sample fallback"
    assert result.warning is not None
    assert "API key" in result.warning

