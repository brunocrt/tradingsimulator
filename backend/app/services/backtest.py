from collections.abc import Sequence

from app.core.config import SimulatorConfig
from app.models.domain import Candle, Decision, OrderStatus, PortfolioState, Position, TradeJournalEntry
from app.services.costs import effective_sell_price, sell_fees
from app.services.execution import simulate_buy
from app.services.orchestrator import scan_symbol
from app.services.risk import validate_signal


def _serialize_candle(candle: Candle) -> dict:
    return {
        "symbol": candle.symbol,
        "timestamp": candle.timestamp,
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
        "volume": candle.volume,
        "timeframe": candle.timeframe,
        "vwap": candle.vwap,
    }


def run_single_symbol_backtest(
    candles: Sequence[Candle],
    average_volume: int,
    spread_pct: float,
    estimated_slippage_pct: float,
    config: SimulatorConfig,
) -> dict:
    portfolio = PortfolioState(initial_capital=config.initial_capital, cash=config.initial_capital)
    signals = []
    rejected = []

    for index in range(50, len(candles)):
        history = candles[: index + 1]
        latest = history[-1]

        if latest.symbol not in portfolio.open_positions:
            best_signal = scan_symbol(history, average_volume, spread_pct, estimated_slippage_pct, config)[0]
            signals.append(best_signal)
            if best_signal.decision == Decision.BUY:
                risk = validate_signal(best_signal, portfolio, config)
                if risk.approved:
                    order = simulate_buy(best_signal, risk.shares, spread_pct, estimated_slippage_pct, portfolio, config)
                    if order.status == OrderStatus.FILLED:
                        portfolio.cash -= order.filled_quantity * order.filled_price + order.fees
                        portfolio.open_positions[latest.symbol] = Position(
                            symbol=latest.symbol,
                            quantity=order.filled_quantity,
                            average_entry_price=order.filled_price,
                            stop_price=best_signal.stop_price,
                            target_price=best_signal.target_price,
                            opened_at=latest.timestamp,
                        )
                    else:
                        rejected.append({"symbol": latest.symbol, "reasons": [order.reason]})
                else:
                    rejected.append({"symbol": latest.symbol, "reasons": risk.reasons})

        position = portfolio.open_positions.get(latest.symbol)
        if position is None:
            continue

        exit_price = None
        exit_reason = ""
        if latest.low <= position.stop_price:
            exit_price = position.stop_price
            exit_reason = "STOP_LOSS"
        elif latest.high >= position.target_price:
            exit_price = position.target_price
            exit_reason = "TAKE_PROFIT"
        elif index == len(candles) - 1:
            exit_price = latest.close
            exit_reason = "END_OF_BACKTEST"

        if exit_price is not None:
            filled_exit, spread_cost, slippage = effective_sell_price(exit_price, spread_pct, estimated_slippage_pct)
            fees = sell_fees(filled_exit, position.quantity, config)
            gross = position.quantity * (filled_exit - position.average_entry_price)
            net = gross - fees
            portfolio.cash += position.quantity * filled_exit - fees
            portfolio.realized_pnl += net
            portfolio.trades.append(
                TradeJournalEntry(
                    symbol=position.symbol,
                    strategy=signals[-1].strategy_name if signals else "UNKNOWN",
                    entry_time=position.opened_at,
                    exit_time=latest.timestamp,
                    entry_price=position.average_entry_price,
                    exit_price=round(filled_exit, 4),
                    shares=position.quantity,
                    gross_pnl=round(gross, 2),
                    net_pnl=round(net, 2),
                    fees=round(fees, 4),
                    slippage=round(slippage + spread_cost, 4),
                    risk_amount=round(position.quantity * (position.average_entry_price - position.stop_price), 2),
                    reward_amount=round(position.quantity * (position.target_price - position.average_entry_price), 2),
                    risk_reward_planned=round(
                        (position.target_price - position.average_entry_price)
                        / max(position.average_entry_price - position.stop_price, 0.01),
                        2,
                    ),
                    risk_reward_realized=round(
                        (filled_exit - position.average_entry_price)
                        / max(position.average_entry_price - position.stop_price, 0.01),
                        2,
                    ),
                    exit_reason=exit_reason,
                    notes=["Costs include spread and slippage assumptions"],
                )
            )
            del portfolio.open_positions[position.symbol]

    wins = [trade for trade in portfolio.trades if trade.net_pnl > 0]
    losses = [trade for trade in portfolio.trades if trade.net_pnl <= 0]
    gross_profit = sum(trade.net_pnl for trade in wins)
    gross_loss = abs(sum(trade.net_pnl for trade in losses))
    total_return = (portfolio.cash - config.initial_capital) / config.initial_capital * 100
    return {
        "portfolio": {
            "initialCapital": config.initial_capital,
            "cash": round(portfolio.cash, 2),
            "equity": round(portfolio.cash, 2),
            "realizedPnl": round(portfolio.realized_pnl, 2),
            "totalReturnPct": round(total_return, 2),
        },
        "performance": {
            "trades": len(portfolio.trades),
            "winRate": round(len(wins) / len(portfolio.trades) * 100, 2) if portfolio.trades else 0,
            "grossProfit": round(gross_profit, 2),
            "grossLoss": round(gross_loss, 2),
            "profitFactor": round(gross_profit / gross_loss, 2) if gross_loss else None,
            "netProfit": round(portfolio.realized_pnl, 2),
        },
        "signals": [signal.to_dict() for signal in signals[-25:]],
        "rejected": rejected[-25:],
        "trades": [trade.__dict__ for trade in portfolio.trades],
        "candles": [_serialize_candle(candle) for candle in candles],
    }
