from collections.abc import Sequence

from app.models.domain import Candle, IndicatorSnapshot


def ema(values: Sequence[float], period: int) -> float:
    if not values:
        return 0.0
    alpha = 2 / (period + 1)
    result = values[0]
    for value in values[1:]:
        result = alpha * value + (1 - alpha) * result
    return result


def rsi(values: Sequence[float], period: int = 14) -> float:
    if len(values) <= period:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    for previous, current in zip(values[-period - 1 : -1], values[-period:]):
        delta = current - previous
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    average_gain = sum(gains) / period
    average_loss = sum(losses) / period
    if average_loss == 0:
        return 100.0
    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def atr(candles: Sequence[Candle], period: int = 14) -> float:
    if len(candles) < 2:
        return 0.0
    ranges: list[float] = []
    window = candles[-period:]
    previous_close = candles[-len(window) - 1].close if len(candles) > len(window) else candles[0].close
    for candle in window:
        ranges.append(
            max(
                candle.high - candle.low,
                abs(candle.high - previous_close),
                abs(candle.low - previous_close),
            )
        )
        previous_close = candle.close
    return sum(ranges) / len(ranges)


def anchored_vwap(candles: Sequence[Candle]) -> float:
    total_volume = sum(candle.volume for candle in candles)
    if total_volume == 0:
        return candles[-1].close if candles else 0.0
    return sum(candle.close * candle.volume for candle in candles) / total_volume


def relative_volume(candles: Sequence[Candle], period: int = 20) -> tuple[float, bool]:
    if len(candles) < 2:
        return 1.0, False
    current = candles[-1].volume
    history = candles[-period - 1 : -1]
    average = sum(candle.volume for candle in history) / max(len(history), 1)
    if average == 0:
        return 1.0, False
    ratio = current / average
    return ratio, current > average


def snapshot(candles: Sequence[Candle], opening_range_minutes: int = 15) -> IndicatorSnapshot:
    if not candles:
        raise ValueError("At least one candle is required to build an indicator snapshot.")
    closes = [candle.close for candle in candles]
    rel_volume, above_average = relative_volume(candles)
    opening_range = candles[:opening_range_minutes] or candles
    latest = candles[-1]
    return IndicatorSnapshot(
        symbol=latest.symbol,
        timestamp=latest.timestamp,
        close=latest.close,
        vwap=anchored_vwap(candles),
        ema_9=ema(closes[-9:], 9),
        ema_20=ema(closes[-20:], 20),
        ema_50=ema(closes[-50:], 50),
        rsi=rsi(closes),
        atr=max(atr(candles), 0.01),
        relative_volume=rel_volume,
        volume_above_average=above_average,
        opening_range_high=max(candle.high for candle in opening_range),
        opening_range_low=min(candle.low for candle in opening_range),
    )

