// #define _WIN32_WINNT 0x0A00

// #include "websocket_client.hpp"

// int main() {
//     run_websocket();
//     return 0;
// }

#include <QApplication>
#include "mainwindow.hpp"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    MainWindow window;
    window.show();

    return app.exec();
}


// #include "fee_calculator.hpp"

// FeeTier tier = FeeTier::TIER1;
// double fee_usd = compute_fee_usd(100.0, tier);
// std::cout << "Expected Fee: $" << fee_usd << std::endl;

// #include "slippage_calculator.hpp"

// double usd_amount = 100.0;  // Input
// OrderSide side = OrderSide::BUY; // market buy

// double slippage = compute_slippage(orderbook, usd_amount, side);
// std::cout << "Expected Slippage: " << slippage << " %" << std::endl;


// #include "market_impact.hpp"

// MarketImpactParams params = {0.0001, 0.00003}; // can be tuned
// double market_impact_cost = compute_market_impact(100.0, params);
// std::cout << "Market Impact Cost: $" << market_impact_cost << std::endl;


// #include "net_cost.hpp"

// // Inputs from previous steps
// double slippage = 0.15;         // example
// double fee = 0.10;              // example
// double market_impact = 0.25;    // example

// NetCostInput net_input = {100.0, slippage, fee, market_impact};
// double net_cost = compute_net_cost(net_input);

// std::cout << "✅ Total Net Cost: $" << net_cost << std::endl;


// #include "maker_taker_estimator.hpp"

// MakerTakerInput maker_input = {
//     true,    // is_market_order
//     0.6,     // volatility
//     0.4,     // order_book_depth
//     0.3      // time_since_last_trade
// };

// MakerTakerResult res = estimate_maker_taker(maker_input);

// std::cout << "📈 Maker probability: " << res.maker_prob << "\n";
// std::cout << "📉 Taker probability: " << res.taker_prob << "\n";
