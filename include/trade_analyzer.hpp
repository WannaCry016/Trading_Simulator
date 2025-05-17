#pragma once

#include <vector>
#include <string>
#include <chrono>
#include <tuple>
#include "orderbook.hpp"
#include "orderside.hpp"

enum class FeeTier {
    TIER1 = 1,
    TIER2 = 2,
    TIER3 = 3
};

struct MakerTakerInput {
    bool is_market_order;
    double volatility;
    double order_book_depth;
    double time_since_last_trade;
};

struct MakerTakerResult {
    double maker_prob;
    double taker_prob;
};

struct MarketImpactParams {
    double eta;
    double gamma;
};

struct NetCostInput {
    double usd_quantity;
    double slippage;
    double fee;
    double market_impact;
};

struct TradeCostResult {
    double slippage;
    double fee;
    double market_impact;
    double net_cost;
    MakerTakerResult maker_taker_result;
};

class LatencyTimer {
public:
    void start();
    long long stop();  // microseconds
private:
    std::chrono::high_resolution_clock::time_point start_time;
};

class TradeAnalyzer {
public:
    TradeAnalyzer(const OrderBook& ob, const std::string& exchange, FeeTier tier);

    double computeSpread() const;
    double computeVolatility(const std::vector<double>& prices) const;
    double computeSlippage(double usd_amount, double volatility, double spread, const std::string& exchange) const;
    double computeFee(double usd_amount) const;
    double computeMarketImpact(double usd_qty, MarketImpactParams params) const;
    MakerTakerResult estimateMakerTaker(const MakerTakerInput& input) const;
    double computeNetCost(const NetCostInput& input) const;
    TradeCostResult analyze(const OrderBook& ob, double usd_amount, FeeTier tier, const MarketImpactParams& mi_params, const MakerTakerInput& mk_input, const std::vector<double>& recent_prices, const std::string& exchange_name) const;

    // Accessor
    const OrderBook& getOrderBook() const;

private:
    OrderBook order_book;
    std::string exchange_name;
    FeeTier fee_tier;
};
