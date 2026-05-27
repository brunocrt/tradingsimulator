from app.core.config import SimulatorConfig
from app.models.domain import LiquiditySnapshot


def evaluate_liquidity(
    symbol: str,
    price: float,
    average_volume: int,
    spread_pct: float,
    estimated_slippage_pct: float,
    config: SimulatorConfig,
) -> LiquiditySnapshot:
    average_dollar_volume = average_volume * price
    failures: list[str] = []
    if spread_pct > config.max_spread_pct:
        failures.append("Spread above configured maximum")
    if estimated_slippage_pct > config.max_estimated_slippage_pct:
        failures.append("Estimated slippage above configured maximum")
    if average_dollar_volume < config.min_average_dollar_volume:
        failures.append("Average dollar volume below minimum")

    spread_score = max(0.0, 1 - spread_pct / max(config.max_spread_pct, 0.01))
    slippage_score = max(0.0, 1 - estimated_slippage_pct / max(config.max_estimated_slippage_pct, 0.01))
    volume_score = min(1.0, average_dollar_volume / config.min_average_dollar_volume)
    score = round((spread_score * 0.4 + slippage_score * 0.3 + volume_score * 0.3), 2)

    return LiquiditySnapshot(
        symbol=symbol,
        spread_pct=spread_pct,
        estimated_slippage_pct=estimated_slippage_pct,
        average_dollar_volume=average_dollar_volume,
        liquidity_score=score,
        tradable=not failures,
        reason=", ".join(failures) if failures else "High liquidity and acceptable spread",
    )

