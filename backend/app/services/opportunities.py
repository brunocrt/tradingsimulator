from dataclasses import asdict, dataclass
from datetime import date

from app.core.config import SimulatorConfig
from app.models.domain import Candle, Decision
from app.services.indicators import snapshot
from app.services.market_data import MarketDataProviderName, MarketDataRequest, average_volume, fetch_market_data
from app.services.orchestrator import scan_symbol


@dataclass(frozen=True)
class Opportunity:
    rank: int
    symbol: str
    status: str
    opportunity_score: int
    momentum_score: int
    setup_score: int
    liquidity_score: int
    best_strategy: str
    decision: str
    entry_price: float
    stop_price: float
    target_price: float
    risk_reward_ratio: float
    return_20d_pct: float
    return_50d_pct: float
    relative_volume: float
    rsi: float
    reasons: list[str]
    data_warning: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def scan_opportunities(
    symbols: list[str],
    provider: MarketDataProviderName,
    start: date,
    end: date,
    timeframe: str,
    api_key: str | None,
    config: SimulatorConfig,
    limit: int = 10,
) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    for symbol in symbols:
        request = MarketDataRequest(
            symbol=symbol.upper(),
            provider=provider,
            start=start,
            end=end,
            timeframe=timeframe,
            api_key=api_key,
        )
        market_data = fetch_market_data(request)
        if len(market_data.candles) < 60:
            continue
        opportunities.append(_rank_symbol(market_data.candles, market_data.warning, config))

    ranked = sorted(opportunities, key=lambda candidate: candidate.opportunity_score, reverse=True)
    return [
        Opportunity(**{**candidate.to_dict(), "rank": index + 1})
        for index, candidate in enumerate(ranked[:limit])
    ]


def _rank_symbol(candles: list[Candle], data_warning: str | None, config: SimulatorConfig) -> Opportunity:
    indicators = snapshot(candles)
    volume = average_volume(candles)
    signals = scan_symbol(
        candles,
        average_volume=volume,
        spread_pct=0.02,
        estimated_slippage_pct=0.03,
        config=config,
    )
    best_signal = signals[0]
    return_20d = _window_return(candles, 20)
    return_50d = _window_return(candles, 50)
    momentum_score = _momentum_score(candles, return_20d, return_50d)
    setup_score = best_signal.score
    liquidity_score = 90 if volume * indicators.close >= config.min_average_dollar_volume else 45
    risk_reward_score = min(100, round(best_signal.risk_reward_ratio / 3 * 100))
    opportunity_score = round(
        setup_score * 0.42
        + momentum_score * 0.32
        + liquidity_score * 0.16
        + risk_reward_score * 0.10
    )
    status = _status(best_signal.decision, opportunity_score, momentum_score)
    reasons = _reasons(best_signal.reasons, return_20d, return_50d, momentum_score, status)

    return Opportunity(
        rank=0,
        symbol=indicators.symbol,
        status=status,
        opportunity_score=opportunity_score,
        momentum_score=momentum_score,
        setup_score=setup_score,
        liquidity_score=liquidity_score,
        best_strategy=best_signal.strategy_name,
        decision=best_signal.decision.value,
        entry_price=best_signal.entry_price,
        stop_price=best_signal.stop_price,
        target_price=best_signal.target_price,
        risk_reward_ratio=best_signal.risk_reward_ratio,
        return_20d_pct=return_20d,
        return_50d_pct=return_50d,
        relative_volume=round(indicators.relative_volume, 2),
        rsi=round(indicators.rsi, 2),
        reasons=reasons,
        data_warning=data_warning,
    )


def _window_return(candles: list[Candle], window: int) -> float:
    if len(candles) <= window:
        return 0.0
    start = candles[-window - 1].close
    if start <= 0:
        return 0.0
    return round((candles[-1].close - start) / start * 100, 2)


def _momentum_score(candles: list[Candle], return_20d: float, return_50d: float) -> int:
    closes = [candle.close for candle in candles]
    latest = snapshot(candles)
    score = 0
    if return_20d > 0:
        score += min(30, round(return_20d * 2))
    if return_50d > 0:
        score += min(25, round(return_50d))
    if latest.ema_9 > latest.ema_20 > latest.ema_50:
        score += 25
    if closes[-1] >= max(closes[-20:]) * 0.97:
        score += 10
    if 50 <= latest.rsi <= 72:
        score += 10
    elif latest.rsi > 78:
        score -= 10
    return max(0, min(score, 100))


def _status(decision: Decision, opportunity_score: int, momentum_score: int) -> str:
    if decision == Decision.BUY and opportunity_score >= 80 and momentum_score >= 55:
        return "TOP_CANDIDATE"
    if opportunity_score >= 70 and momentum_score >= 45:
        return "WATCH"
    return "IGNORE"


def _reasons(
    signal_reasons: list[str],
    return_20d: float,
    return_50d: float,
    momentum_score: int,
    status: str,
) -> list[str]:
    reasons = signal_reasons[:2]
    if return_20d > 0:
        reasons.append(f"20-period momentum is positive at {return_20d}%")
    if return_50d > 0:
        reasons.append(f"50-period momentum is positive at {return_50d}%")
    if momentum_score < 45:
        reasons.append("Momentum is not strong enough to prioritize over better candidates")
    if status == "IGNORE":
        reasons.append("Opportunity score is below the capital allocation threshold")
    return reasons[:5]
