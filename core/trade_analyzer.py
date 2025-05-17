import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class FeeTier(Enum):
    TIER1 = 1
    TIER2 = 2
    TIER3 = 3


@dataclass
class MarketImpactParams:
    eta: float          # Temporary impact coefficient
    gamma: float        # Permanent impact coefficient
    lambda_: float      # Risk aversion
    sigma: float        # Volatility
    alpha: float = 1.0  # Temporary impact exponent
    beta: float = 1.0   # Permanent impact exponent


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class OrderLevel:
    price: float
    quantity: float

@dataclass
class OrderBook:
    asks: List[OrderLevel] = field(default_factory=list)
    bids: List[OrderLevel] = field(default_factory=list)

@dataclass
class MakerTakerInput:
    is_market_order: bool
    volatility: float
    order_book_depth: float
    time_since_last_trade: float


@dataclass
class MakerTakerResult:
    maker_prob: float
    taker_prob: float


@dataclass
class NetCostInput:
    usd_amount: float
    slippage: float
    fee: float
    market_impact: float


@dataclass
class TradeCostResult:
    slippage: float
    fee: float
    market_impact: float
    net_cost: float
    maker_taker_result: MakerTakerResult


class TradeAnalyzer:
    def __init__(self, order_book, exchange_name: str, fee_tier: FeeTier):
        self.order_book = order_book
        self.exchange_name = exchange_name
        self.fee_tier = fee_tier

    def get_order_book(self):
        return self.order_book

    def compute_spread(self) -> float:
        if not self.order_book.bids or not self.order_book.asks:
            return 0.0
        return self.order_book.asks[0].price - self.order_book.bids[0].price

    def compute_market_impact(self, usd_qty: float, params: MarketImpactParams) -> float:
        temp_impact = params.eta * usd_qty ** params.alpha
        perm_impact = params.gamma * usd_qty ** params.beta
        execution_risk = 0.5 * params.lambda_ ** 2 * params.sigma ** 2 * usd_qty ** 2
        return temp_impact + perm_impact + execution_risk


    def compute_slippage(self, usd_amount: float, volatility: float, spread: float, exchange: str) -> float:
        # Dummy linear regression coefficients for OKX
        beta0 = 0.01  # base slippage
        beta1 = 0.12  # log(order size)
        beta2 = 0.6   # volatility weight
        beta3 = 0.25  # spread weight

        # Customize for other exchanges if needed
        # if exchange == "BINANCE":
        #     beta0, beta1, beta2, beta3 = ...

        log_order = math.log(usd_amount)
        return beta0 + beta1 * log_order + beta2 * volatility + beta3 * spread

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    @staticmethod
    def get_taker_fee_percent(tier: FeeTier) -> float:
        if tier == FeeTier.TIER1:
            return 0.001
        elif tier == FeeTier.TIER2:
            return 0.0005
        elif tier == FeeTier.TIER3:
            return 0.0001
        return 0.001

    def compute_fee(self, usd_amount: float) -> float:
        fee_percent = self.get_taker_fee_percent(self.fee_tier)
        return usd_amount * fee_percent

    def compute_market_impact(self, usd_qty: float, params: MarketImpactParams) -> float:
        temporary_impact = params.eta * usd_qty
        permanent_impact = params.gamma * usd_qty
        execution_risk = 0.5 * params.lambda_ * (params.sigma ** 2) * (usd_qty ** 2)
        return temporary_impact + permanent_impact + execution_risk
    
    def compute_volatility(self, prices: List[float]) -> float:
        if len(prices) < 2:
            return 0.0
        log_returns = [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]
        mean = sum(log_returns) / len(log_returns)
        variance = sum((r - mean) ** 2 for r in log_returns) / len(log_returns)
        return math.sqrt(variance)


    def estimate_maker_taker(self, input_data: MakerTakerInput) -> MakerTakerResult:
        w_market = 2.0
        w_volatility = 1.5
        w_depth = -1.0
        w_time = -0.5

        score = 0.0
        score += w_market * (1.0 if input_data.is_market_order else 0.0)
        score += w_volatility * input_data.volatility
        score += w_depth * input_data.order_book_depth
        score += w_time * input_data.time_since_last_trade

        taker_prob = self._sigmoid(score)
        maker_prob = 1.0 - taker_prob

        return MakerTakerResult(maker_prob, taker_prob)

    def compute_net_cost(self, input_data: NetCostInput) -> float:
        return input_data.slippage + input_data.fee + input_data.market_impact

    def analyze(self, order_book, usd_amount: float, fee_tier: FeeTier,
                mi_params: MarketImpactParams, mk_input: MakerTakerInput,
                recent_prices: List[float], exchange_name: str) -> TradeCostResult:
        self.order_book = order_book
        self.fee_tier = fee_tier
        self.exchange_name = exchange_name

        spread = self.compute_spread()
        volatility = self.compute_volatility(recent_prices)
        slippage = self.compute_slippage(usd_amount, volatility, spread, exchange_name)
        fee = self.compute_fee(usd_amount)
        market_impact = self.compute_market_impact(usd_amount, mi_params)

        net_input = NetCostInput(usd_amount, slippage, fee, market_impact)
        net_cost = self.compute_net_cost(net_input)

        maker_taker_result = self.estimate_maker_taker(mk_input)

        return TradeCostResult(slippage, fee, market_impact, net_cost, maker_taker_result)
