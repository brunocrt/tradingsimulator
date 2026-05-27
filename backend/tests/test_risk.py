from datetime import datetime

from app.core.config import SimulatorConfig
from app.models.domain import Decision, EntryQuality, PortfolioState, Signal
from app.services.risk import validate_signal


def test_validate_signal_sizes_position_from_risk_budget() -> None:
    config = SimulatorConfig(initial_capital=10_000, risk_per_trade_pct=1.0)
    portfolio = PortfolioState(initial_capital=10_000, cash=10_000)
    signal = Signal(
        symbol="AMD",
        timestamp=datetime(2026, 5, 26, 10, 30),
        strategy_name="VWAP_PULLBACK",
        decision=Decision.BUY,
        confidence=0.8,
        entry_price=50,
        stop_price=49,
        target_price=52,
        risk_reward_ratio=2.0,
        score=82,
        crowding_score=30,
        trap_risk_score=20,
        entry_quality=EntryQuality.GOOD,
        status="APPROVED",
    )

    decision = validate_signal(signal, portfolio, config)

    assert decision.approved
    assert decision.shares == 50
    assert decision.risk_amount == 50
    assert decision.estimated_position_cost == 2500


def test_validate_signal_rejects_poor_risk_reward() -> None:
    config = SimulatorConfig(minimum_risk_reward_ratio=1.5)
    portfolio = PortfolioState(initial_capital=10_000, cash=10_000)
    signal = Signal(
        symbol="AMD",
        timestamp=datetime(2026, 5, 26, 10, 30),
        strategy_name="VWAP_PULLBACK",
        decision=Decision.BUY,
        confidence=0.8,
        entry_price=50,
        stop_price=49,
        target_price=51,
        risk_reward_ratio=1.0,
        score=82,
        crowding_score=30,
        trap_risk_score=20,
        entry_quality=EntryQuality.GOOD,
        status="APPROVED",
    )

    decision = validate_signal(signal, portfolio, config)

    assert not decision.approved
    assert "Risk/reward below configured minimum" in decision.reasons

