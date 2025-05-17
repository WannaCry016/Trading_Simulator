#include "trade_analyzer.hpp"
#include <cmath>
#include <numeric>
#include <stdexcept>

void LatencyTimer::start() {
    start_time = std::chrono::high_resolution_clock::now();
}

long long LatencyTimer::stop() {
    auto end_time = std::chrono::high_resolution_clock::now();
    return std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count();
}

TradeAnalyzer::TradeAnalyzer(const OrderBook& ob, const std::string& exchange, FeeTier tier)
    : order_book(ob), exchange_name(exchange), fee_tier(tier) {}

    const OrderBook& TradeAnalyzer::getOrderBook() const {
        return order_book;
}

double TradeAnalyzer::computeSpread() const {
    if (order_book.bids.empty() || order_book.asks.empty()) return 0.0;
    return order_book.asks.front().price - order_book.bids.front().price;
}

double TradeAnalyzer::computeVolatility(const std::vector<double>& prices) const {
    if (prices.size() < 2) return 0.0;

    std::vector<double> log_returns;
    for (size_t i = 1; i < prices.size(); ++i)
        log_returns.push_back(std::log(prices[i] / prices[i - 1]));

    double mean = std::accumulate(log_returns.begin(), log_returns.end(), 0.0) / log_returns.size();
    double variance = 0.0;
    for (double r : log_returns)
        variance += (r - mean) * (r - mean);

    variance /= log_returns.size();
    return std::sqrt(variance);
}

double TradeAnalyzer::computeSlippage(
    double usd_amount,
    double volatility,
    double spread,
    const std::string& exchange
) const {
    // Dummy linear regression coefficients for OKX
    const double beta0 = 0.01;   // base slippage
    const double beta1 = 0.12;   // log(order size)
    const double beta2 = 0.6;    // volatility weight
    const double beta3 = 0.25;   // spread weight

    // You could customize coefficients based on exchange if needed
    // if (exchange == "BINANCE") { ... }

    double log_order = std::log(usd_amount);
    return beta0 + beta1 * log_order + beta2 * volatility + beta3 * spread;
}

static double sigmoid(double x) {
    return 1.0 / (1.0 + std::exp(-x));
}

double get_taker_fee_percent(FeeTier tier) {
    switch (tier) {
        case FeeTier::TIER1: return 0.001;
        case FeeTier::TIER2: return 0.0005;
        case FeeTier::TIER3: return 0.0001;
    }
    return 0.001;
}

double TradeAnalyzer::computeFee(double usd_amount) const {
    double fee_percent = get_taker_fee_percent(fee_tier);
    return usd_amount * fee_percent;
}

double TradeAnalyzer::computeMarketImpact(double usd_qty, MarketImpactParams params) const {
    return params.eta * usd_qty + params.gamma * usd_qty * usd_qty;
}

MakerTakerResult TradeAnalyzer::estimateMakerTaker(const MakerTakerInput& input) const {
    // Heuristic weights
    double w_market = 2.0;
    double w_volatility = 1.5;
    double w_depth = -1.0;
    double w_time = -0.5;

    double score = 0.0;
    score += w_market * (input.is_market_order ? 1.0 : 0.0);
    score += w_volatility * input.volatility;
    score += w_depth * input.order_book_depth;
    score += w_time * input.time_since_last_trade;

    // Convert score to probability using sigmoid
    double taker_prob = sigmoid(score);
    double maker_prob = 1.0 - taker_prob;

    return {maker_prob, taker_prob};
}

double TradeAnalyzer::computeNetCost(const NetCostInput& input) const {
    return input.slippage + input.fee + input.market_impact;
}

TradeCostResult TradeAnalyzer::analyze(const OrderBook& ob,
                                       double usd_amount,
                                       FeeTier tier,
                                       const MarketImpactParams& mi_params,
                                       const MakerTakerInput& mk_input,
                                       const std::vector<double>& recent_prices,
                                       const std::string& exchange_name) const {
    double spread = computeSpread();
    double volatility = computeVolatility(recent_prices);
    double slippage = computeSlippage(usd_amount, volatility, spread, exchange_name);
    double fee = computeFee(usd_amount);
    double market_impact = computeMarketImpact(usd_amount, mi_params);

    NetCostInput net_input{usd_amount, slippage, fee, market_impact};
    double net_cost = computeNetCost(net_input);

    MakerTakerResult maker_taker_result = estimateMakerTaker(mk_input);

    return TradeCostResult{
        slippage,
        fee,
        market_impact,
        net_cost,
        maker_taker_result
    };
}
