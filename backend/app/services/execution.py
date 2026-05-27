from app.core.config import SimulatorConfig
from app.models.domain import OrderStatus, PortfolioState, Signal, SimulatedOrder
from app.services.costs import effective_buy_price


def simulate_buy(
    signal: Signal,
    shares: int,
    spread_pct: float,
    slippage_pct: float,
    portfolio: PortfolioState,
    config: SimulatorConfig,
) -> SimulatedOrder:
    filled_price, spread_cost, slippage = effective_buy_price(signal.entry_price, spread_pct, slippage_pct)
    notional = filled_price * shares
    fees = config.commission_per_trade
    if shares <= 0:
        return SimulatedOrder(
            symbol=signal.symbol,
            side="BUY",
            requested_quantity=shares,
            filled_quantity=0,
            requested_price=signal.entry_price,
            filled_price=0.0,
            status=OrderStatus.REJECTED,
            slippage_amount=0.0,
            spread_cost=0.0,
            fees=0.0,
            created_at=signal.timestamp,
            filled_at=None,
            reason="No shares requested",
        )
    if notional + fees > portfolio.cash:
        return SimulatedOrder(
            symbol=signal.symbol,
            side="BUY",
            requested_quantity=shares,
            filled_quantity=0,
            requested_price=signal.entry_price,
            filled_price=0.0,
            status=OrderStatus.REJECTED,
            slippage_amount=slippage,
            spread_cost=spread_cost,
            fees=fees,
            created_at=signal.timestamp,
            filled_at=None,
            reason="Insufficient cash after costs",
        )
    return SimulatedOrder(
        symbol=signal.symbol,
        side="BUY",
        requested_quantity=shares,
        filled_quantity=shares,
        requested_price=signal.entry_price,
        filled_price=round(filled_price, 4),
        status=OrderStatus.FILLED,
        slippage_amount=round(slippage, 4),
        spread_cost=round(spread_cost, 4),
        fees=round(fees, 4),
        created_at=signal.timestamp,
        filled_at=signal.timestamp,
    )

