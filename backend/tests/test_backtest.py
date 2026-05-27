from app.core.config import SimulatorConfig
from app.services.backtest import run_single_symbol_backtest
from app.services.sample_data import generate_intraday_candles, sample_average_volume


def test_backtest_can_start_from_1000_dollars() -> None:
    result = run_single_symbol_backtest(
        generate_intraday_candles("AMD"),
        average_volume=sample_average_volume(),
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=SimulatorConfig(initial_capital=1000),
    )

    assert result["portfolio"]["initialCapital"] == 1000
    assert result["portfolio"]["cash"] >= 0


def test_backtest_returns_cost_aware_trade_journal() -> None:
    result = run_single_symbol_backtest(
        generate_intraday_candles("AMD"),
        average_volume=sample_average_volume(),
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=SimulatorConfig(),
    )

    assert "portfolio" in result
    assert "performance" in result
    assert "signals" in result
    assert "trades" in result
    for trade in result["trades"]:
        assert trade["fees"] >= 0
        assert trade["slippage"] >= 0
        assert trade["net_pnl"] <= trade["gross_pnl"]
