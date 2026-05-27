from app.core.config import SimulatorConfig


def effective_buy_price(entry_price: float, spread_pct: float, slippage_pct: float) -> tuple[float, float, float]:
    half_spread = entry_price * (spread_pct / 100) / 2
    slippage = entry_price * (slippage_pct / 100)
    return entry_price + half_spread + slippage, half_spread, slippage


def effective_sell_price(exit_price: float, spread_pct: float, slippage_pct: float) -> tuple[float, float, float]:
    half_spread = exit_price * (spread_pct / 100) / 2
    slippage = exit_price * (slippage_pct / 100)
    return exit_price - half_spread - slippage, half_spread, slippage


def sell_fees(price: float, shares: int, config: SimulatorConfig) -> float:
    notional = price * shares
    return config.commission_per_trade + (notional * config.sec_fee_pct_on_sell) + (
        shares * config.finra_fee_per_share_on_sell
    )

