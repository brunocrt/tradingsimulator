from dataclasses import dataclass, field


DEFAULT_WATCHLIST = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMD",
    "META",
    "AMZN",
    "GOOGL",
    "TSLA",
    "NFLX",
    "AVGO",
    "JPM",
    "BAC",
    "XOM",
    "CVX",
    "UNH",
    "COST",
    "CRM",
    "ORCL",
    "INTC",
    "QQQ",
    "SPY",
]

DEFAULT_DISCOVERY_UNIVERSE = [
    "AAPL",
    "ABBV",
    "ABT",
    "ACN",
    "ADBE",
    "AMD",
    "AMGN",
    "AMT",
    "AMZN",
    "ANET",
    "ARM",
    "ASML",
    "AVGO",
    "AXP",
    "BA",
    "BAC",
    "BKNG",
    "BLK",
    "BRK-B",
    "CAT",
    "COST",
    "CRM",
    "CRWD",
    "CSCO",
    "CVX",
    "DE",
    "DIA",
    "DIS",
    "ELV",
    "ETN",
    "GE",
    "GOOG",
    "GOOGL",
    "GS",
    "HD",
    "HON",
    "IBM",
    "INTC",
    "INTU",
    "ISRG",
    "IWM",
    "JPM",
    "KO",
    "LIN",
    "LLY",
    "LMT",
    "LOW",
    "MA",
    "MCD",
    "MDT",
    "META",
    "MRK",
    "MS",
    "MSFT",
    "MU",
    "NFLX",
    "NKE",
    "NOW",
    "NVDA",
    "ORCL",
    "PANW",
    "PEP",
    "PFE",
    "PG",
    "PLTR",
    "QQQ",
    "REGN",
    "RTX",
    "SHOP",
    "SMCI",
    "SNOW",
    "SPY",
    "T",
    "TEAM",
    "TMO",
    "TSLA",
    "TXN",
    "UBER",
    "UNH",
    "UNP",
    "UPS",
    "V",
    "VRTX",
    "VZ",
    "WFC",
    "WMT",
    "XOM",
]


@dataclass(frozen=True)
class SimulatorConfig:
    initial_capital: float = 10_000.0
    risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 2.0
    max_total_drawdown_pct: float = 10.0
    max_open_positions: int = 3
    max_trades_per_day: int = 5
    max_consecutive_losses: int = 3
    max_capital_deployed_pct: float = 75.0
    max_single_position_pct: float = 25.0
    minimum_signal_score: int = 75
    minimum_risk_reward_ratio: float = 1.5
    preferred_risk_reward_ratio: float = 2.0
    max_spread_pct: float = 0.05
    max_estimated_slippage_pct: float = 0.10
    min_average_dollar_volume: float = 20_000_000.0
    default_take_profit_r_multiple: float = 2.0
    default_stop_loss_atr_multiple: float = 1.2
    commission_per_trade: float = 0.0
    sec_fee_pct_on_sell: float = 0.000008
    finra_fee_per_share_on_sell: float = 0.000166
    allow_fractional_shares: bool = False
    enabled_strategies: tuple[str, ...] = (
        "VWAP_PULLBACK",
        "OPENING_RANGE_BREAKOUT",
        "TREND_CONTINUATION",
    )
    watchlist: list[str] = field(default_factory=lambda: DEFAULT_WATCHLIST.copy())
    discovery_universe: list[str] = field(default_factory=lambda: DEFAULT_DISCOVERY_UNIVERSE.copy())
