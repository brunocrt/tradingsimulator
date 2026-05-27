from dataclasses import dataclass
from math import floor

from app.core.config import SimulatorConfig
from app.models.domain import PortfolioState, Signal


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    shares: int
    risk_amount: float
    estimated_position_cost: float
    reasons: list[str]


def validate_signal(signal: Signal, portfolio: PortfolioState, config: SimulatorConfig) -> RiskDecision:
    reasons: list[str] = []
    risk_per_share = signal.entry_price - signal.stop_price
    if risk_per_share <= 0:
        reasons.append("Stop loss must be below entry for a long trade")
        return RiskDecision(False, 0, 0.0, 0.0, reasons)

    if signal.risk_reward_ratio < config.minimum_risk_reward_ratio:
        reasons.append("Risk/reward below configured minimum")
    if signal.score < config.minimum_signal_score:
        reasons.append("Signal score below approval threshold")
    if len(portfolio.open_positions) >= config.max_open_positions:
        reasons.append("Maximum open positions reached")
    if len(portfolio.trades) >= config.max_trades_per_day:
        reasons.append("Maximum trades per day reached")

    dollar_risk = portfolio.equity * (config.risk_per_trade_pct / 100)
    shares = dollar_risk / risk_per_share
    if not config.allow_fractional_shares:
        shares = floor(shares)

    max_position_cost = portfolio.equity * (config.max_single_position_pct / 100)
    position_cost = shares * signal.entry_price
    if position_cost > max_position_cost:
        shares = floor(max_position_cost / signal.entry_price)
        position_cost = shares * signal.entry_price

    if position_cost > portfolio.cash:
        shares = floor(portfolio.cash / signal.entry_price)
        position_cost = shares * signal.entry_price

    if shares <= 0:
        reasons.append("Position size would be zero after capital limits")

    return RiskDecision(
        approved=not reasons,
        shares=int(shares),
        risk_amount=round(int(shares) * risk_per_share, 2),
        estimated_position_cost=round(position_cost, 2),
        reasons=reasons,
    )

