from app.services.ticker_master import Ticker, _parse_nasdaq_listed, _parse_other_listed, exchange_universe_symbols


def test_parse_nasdaq_listed_filters_test_issues() -> None:
    payload = "\n".join(
        [
            "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares",
            "AAPL|Apple Inc.|Q|N|N|100|N|N",
            "TEST|Test Corp.|Q|Y|N|100|N|N",
            "File Creation Time: 0527202618:00|||||||",
        ]
    )

    tickers = _parse_nasdaq_listed(payload, "2026-05-27T18:00:00+00:00")

    assert [ticker.symbol for ticker in tickers] == ["AAPL"]
    assert tickers[0].exchange == "NASDAQ"


def test_parse_other_listed_keeps_nyse_and_normalizes_class_symbols() -> None:
    payload = "\n".join(
        [
            "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol",
            "BRK/B|Berkshire Hathaway Inc.|N|BRK/B|N|100|N|BRK/B",
            "SPY|SPDR S&P 500 ETF|P|SPY|Y|100|N|SPY",
            "File Creation Time: 0527202618:00|||||||",
        ]
    )

    tickers = _parse_other_listed(payload, "2026-05-27T18:00:00+00:00")

    assert [ticker.symbol for ticker in tickers] == ["BRK-B"]
    assert tickers[0].exchange == "NYSE"


def test_exchange_universe_prioritizes_liquid_discovery_symbols(tmp_path) -> None:
    path = tmp_path / "ticker_master.csv"
    refreshed_at = "2026-05-27T18:00:00+00:00"
    from app.services.ticker_master import _write_tickers

    _write_tickers(
        [
            Ticker("A", "Agilent", "NYSE", False, "test", refreshed_at),
            Ticker("AAPL", "Apple", "NASDAQ", False, "test", refreshed_at),
            Ticker("MSFT", "Microsoft", "NASDAQ", False, "test", refreshed_at),
        ],
        path,
    )

    assert exchange_universe_symbols(path=path, max_symbols=3) == ["AAPL", "MSFT", "A"]
