from datetime import date

from app.core.config import SimulatorConfig
from app.services.market_data import MarketDataProviderName
from app.services.opportunities import scan_opportunities


def test_opportunity_scanner_ranks_requested_universe() -> None:
    opportunities = scan_opportunities(
        symbols=["AMD", "AAPL", "MSFT"],
        provider=MarketDataProviderName.SAMPLE,
        start=date(2024, 1, 1),
        end=date(2024, 6, 30),
        timeframe="1d",
        api_key=None,
        config=SimulatorConfig(),
        limit=2,
    )

    assert len(opportunities) == 2
    assert [candidate.rank for candidate in opportunities] == [1, 2]
    assert opportunities[0].opportunity_score >= opportunities[1].opportunity_score
    assert opportunities[0].symbol in {"AMD", "AAPL", "MSFT"}
    assert opportunities[0].best_strategy
