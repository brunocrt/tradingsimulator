from datetime import datetime, timedelta
from math import sin

from app.models.domain import Candle


def generate_intraday_candles(symbol: str = "AMD", count: int = 180) -> list[Candle]:
    start = datetime(2026, 5, 26, 9, 30)
    candles: list[Candle] = []
    price = 124.0
    for index in range(count):
        drift = 0.035 if index > 35 else 0.01
        pullback = -0.12 if 65 <= index <= 75 else 0.0
        wave = sin(index / 8) * 0.08
        open_price = price
        close = max(1.0, price + drift + pullback + wave)
        high = max(open_price, close) + 0.18
        low = min(open_price, close) - 0.16
        volume = 180_000 + (index % 20) * 9_000
        if index in (40, 76, 95):
            volume *= 2
        candles.append(
            Candle(
                symbol=symbol,
                timestamp=start + timedelta(minutes=index),
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close, 2),
                volume=volume,
            )
        )
        price = close
    return candles


def sample_average_volume() -> int:
    return 55_000_000

