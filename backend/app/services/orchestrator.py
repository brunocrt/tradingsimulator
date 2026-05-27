from collections.abc import Sequence

from app.core.config import SimulatorConfig
from app.models.domain import Candle, Signal
from app.services.indicators import snapshot
from app.services.liquidity import evaluate_liquidity
from app.strategies.rules import opening_range_breakout, trend_continuation, vwap_pullback


STRATEGIES = {
    "VWAP_PULLBACK": vwap_pullback,
    "OPENING_RANGE_BREAKOUT": opening_range_breakout,
    "TREND_CONTINUATION": trend_continuation,
}


def scan_symbol(
    candles: Sequence[Candle],
    average_volume: int,
    spread_pct: float,
    estimated_slippage_pct: float,
    config: SimulatorConfig,
) -> list[Signal]:
    indicators = snapshot(candles)
    liquidity = evaluate_liquidity(
        indicators.symbol,
        indicators.close,
        average_volume,
        spread_pct,
        estimated_slippage_pct,
        config,
    )
    signals: list[Signal] = []
    for strategy_name in config.enabled_strategies:
        strategy = STRATEGIES.get(strategy_name)
        if strategy is None:
            continue
        signals.append(strategy(indicators, liquidity, config))
    return sorted(signals, key=lambda signal: signal.score, reverse=True)

