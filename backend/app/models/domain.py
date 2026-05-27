from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum


class Decision(StrEnum):
    BUY = "BUY"
    HOLD = "HOLD"
    WAIT = "WAIT"
    REJECTED = "REJECTED"


class EntryQuality(StrEnum):
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class OrderStatus(StrEnum):
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str = "1m"
    vwap: float | None = None


@dataclass(frozen=True)
class IndicatorSnapshot:
    symbol: str
    timestamp: datetime
    close: float
    vwap: float
    ema_9: float
    ema_20: float
    ema_50: float
    rsi: float
    atr: float
    relative_volume: float
    volume_above_average: bool
    opening_range_high: float
    opening_range_low: float


@dataclass(frozen=True)
class LiquiditySnapshot:
    symbol: str
    spread_pct: float
    estimated_slippage_pct: float
    average_dollar_volume: float
    liquidity_score: float
    tradable: bool
    reason: str


@dataclass(frozen=True)
class Signal:
    symbol: str
    timestamp: datetime
    strategy_name: str
    decision: Decision
    confidence: float
    entry_price: float
    stop_price: float
    target_price: float
    risk_reward_ratio: float
    score: int
    crowding_score: int
    trap_risk_score: int
    entry_quality: EntryQuality
    status: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SimulatedOrder:
    symbol: str
    side: str
    requested_quantity: int
    filled_quantity: int
    requested_price: float
    filled_price: float
    status: OrderStatus
    slippage_amount: float
    spread_cost: float
    fees: float
    created_at: datetime
    filled_at: datetime | None
    reason: str = ""


@dataclass
class Position:
    symbol: str
    quantity: int
    average_entry_price: float
    stop_price: float
    target_price: float
    opened_at: datetime
    trailing_stop_price: float | None = None


@dataclass(frozen=True)
class TradeJournalEntry:
    symbol: str
    strategy: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    shares: int
    gross_pnl: float
    net_pnl: float
    fees: float
    slippage: float
    risk_amount: float
    reward_amount: float
    risk_reward_planned: float
    risk_reward_realized: float
    exit_reason: str
    notes: list[str] = field(default_factory=list)


@dataclass
class PortfolioState:
    initial_capital: float
    cash: float
    realized_pnl: float = 0.0
    open_positions: dict[str, Position] = field(default_factory=dict)
    trades: list[TradeJournalEntry] = field(default_factory=list)

    @property
    def equity(self) -> float:
        return self.cash + sum(
            position.quantity * position.average_entry_price
            for position in self.open_positions.values()
        )

