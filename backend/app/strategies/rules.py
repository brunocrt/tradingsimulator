from app.core.config import SimulatorConfig
from app.models.domain import Decision, EntryQuality, IndicatorSnapshot, LiquiditySnapshot, Signal


def _entry_quality(indicators: IndicatorSnapshot, config: SimulatorConfig) -> tuple[EntryQuality, list[str], int]:
    reasons: list[str] = []
    distance_from_vwap_atr = abs(indicators.close - indicators.vwap) / indicators.atr
    if distance_from_vwap_atr > 2.0:
        reasons.append("Entry is extended from VWAP")
        return EntryQuality.POOR, reasons, 25
    if distance_from_vwap_atr > 1.25:
        reasons.append("Entry is moderately extended from VWAP")
        return EntryQuality.FAIR, reasons, 10
    return EntryQuality.GOOD, ["Entry remains near a controlled risk level"], 0


def _base_scores(indicators: IndicatorSnapshot, liquidity: LiquiditySnapshot) -> tuple[int, list[str], int, int]:
    score = 0
    reasons: list[str] = []

    if indicators.close > indicators.vwap and indicators.ema_9 > indicators.ema_20:
        score += 20
        reasons.append("Price is above VWAP with EMA9 above EMA20")
    if 45 <= indicators.rsi <= 70:
        score += 15
        reasons.append("RSI is in the preferred momentum range")
    if indicators.relative_volume >= 1.3 and indicators.volume_above_average:
        score += 15
        reasons.append("Relative volume confirms the setup")
    if liquidity.tradable:
        score += round(liquidity.liquidity_score * 10)
        reasons.append(liquidity.reason)

    crowding_score = 35
    trap_risk_score = 20
    if indicators.close > indicators.vwap + indicators.atr * 1.5:
        crowding_score += 30
        trap_risk_score += 15
        reasons.append("Anti-chase overlay detected extension after signal")
    if not liquidity.tradable:
        trap_risk_score += 20
        reasons.append(liquidity.reason)

    return score, reasons, min(crowding_score, 100), min(trap_risk_score, 100)


def vwap_pullback(indicators: IndicatorSnapshot, liquidity: LiquiditySnapshot, config: SimulatorConfig) -> Signal:
    score, reasons, crowding_score, trap_risk_score = _base_scores(indicators, liquidity)
    entry_quality, entry_reasons, penalty = _entry_quality(indicators, config)
    score += 20 if indicators.close >= indicators.vwap and indicators.close <= indicators.ema_20 + indicators.atr else 0
    score += 15 if entry_quality == EntryQuality.GOOD else 5 if entry_quality == EntryQuality.FAIR else 0
    score += 10 if crowding_score <= 70 else 0
    score += 5 if trap_risk_score <= 60 else 0
    score -= penalty
    reasons.extend(entry_reasons)

    stop_price = min(indicators.vwap, indicators.close - config.default_stop_loss_atr_multiple * indicators.atr)
    target_price = indicators.close + (indicators.close - stop_price) * config.default_take_profit_r_multiple
    risk_reward = (target_price - indicators.close) / max(indicators.close - stop_price, 0.01)
    approved = (
        score >= config.minimum_signal_score
        and liquidity.tradable
        and crowding_score <= 70
        and trap_risk_score <= 60
        and entry_quality != EntryQuality.POOR
    )
    return Signal(
        symbol=indicators.symbol,
        timestamp=indicators.timestamp,
        strategy_name="VWAP_PULLBACK",
        decision=Decision.BUY if approved else Decision.WAIT,
        confidence=round(min(score, 100) / 100, 2),
        entry_price=round(indicators.close, 2),
        stop_price=round(stop_price, 2),
        target_price=round(target_price, 2),
        risk_reward_ratio=round(risk_reward, 2),
        score=max(0, min(score, 100)),
        crowding_score=crowding_score,
        trap_risk_score=trap_risk_score,
        entry_quality=entry_quality,
        status="APPROVED" if approved else "WAIT",
        reasons=reasons,
    )


def opening_range_breakout(
    indicators: IndicatorSnapshot, liquidity: LiquiditySnapshot, config: SimulatorConfig
) -> Signal:
    score, reasons, crowding_score, trap_risk_score = _base_scores(indicators, liquidity)
    broke_range = indicators.close > indicators.opening_range_high
    if broke_range:
        score += 25
        reasons.append("Price broke above the opening range high")
    else:
        reasons.append("Price has not broken the opening range high")

    entry_quality, entry_reasons, penalty = _entry_quality(indicators, config)
    score += 15 if entry_quality == EntryQuality.GOOD else 5 if entry_quality == EntryQuality.FAIR else 0
    score -= penalty
    reasons.extend(entry_reasons)

    stop_price = max(indicators.opening_range_low, indicators.opening_range_high - indicators.atr)
    target_price = indicators.close + (indicators.close - stop_price) * config.default_take_profit_r_multiple
    risk_reward = (target_price - indicators.close) / max(indicators.close - stop_price, 0.01)
    approved = (
        broke_range
        and score >= config.minimum_signal_score
        and liquidity.tradable
        and entry_quality != EntryQuality.POOR
        and crowding_score <= 70
        and trap_risk_score <= 60
    )
    return Signal(
        symbol=indicators.symbol,
        timestamp=indicators.timestamp,
        strategy_name="OPENING_RANGE_BREAKOUT",
        decision=Decision.BUY if approved else Decision.WAIT,
        confidence=round(min(score, 100) / 100, 2),
        entry_price=round(indicators.close, 2),
        stop_price=round(stop_price, 2),
        target_price=round(target_price, 2),
        risk_reward_ratio=round(risk_reward, 2),
        score=max(0, min(score, 100)),
        crowding_score=crowding_score,
        trap_risk_score=trap_risk_score,
        entry_quality=entry_quality,
        status="APPROVED" if approved else "WAIT",
        reasons=reasons,
    )


def trend_continuation(indicators: IndicatorSnapshot, liquidity: LiquiditySnapshot, config: SimulatorConfig) -> Signal:
    score, reasons, crowding_score, trap_risk_score = _base_scores(indicators, liquidity)
    aligned = indicators.close > indicators.vwap and indicators.ema_9 > indicators.ema_20 > indicators.ema_50
    if aligned:
        score += 30
        reasons.append("EMA stack confirms trend continuation")
    entry_quality, entry_reasons, penalty = _entry_quality(indicators, config)
    score += 10 if entry_quality == EntryQuality.GOOD else 0
    score -= penalty
    reasons.extend(entry_reasons)

    stop_price = indicators.ema_20 - indicators.atr * 0.5
    target_price = indicators.close + (indicators.close - stop_price) * config.default_take_profit_r_multiple
    risk_reward = (target_price - indicators.close) / max(indicators.close - stop_price, 0.01)
    approved = aligned and score >= config.minimum_signal_score and liquidity.tradable and entry_quality != EntryQuality.POOR
    return Signal(
        symbol=indicators.symbol,
        timestamp=indicators.timestamp,
        strategy_name="TREND_CONTINUATION",
        decision=Decision.BUY if approved else Decision.WAIT,
        confidence=round(min(score, 100) / 100, 2),
        entry_price=round(indicators.close, 2),
        stop_price=round(stop_price, 2),
        target_price=round(target_price, 2),
        risk_reward_ratio=round(risk_reward, 2),
        score=max(0, min(score, 100)),
        crowding_score=crowding_score,
        trap_risk_score=trap_risk_score,
        entry_quality=entry_quality,
        status="APPROVED" if approved else "WAIT",
        reasons=reasons,
    )

