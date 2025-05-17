#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast/ssl.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/ssl/error.hpp>
#include <boost/asio/ssl/stream.hpp>
#include <iostream>
#include <string>
#include "json.hpp"
#include "trade_analyzer.hpp"

namespace beast = boost::beast;
namespace websocket = beast::websocket;
namespace net = boost::asio;
namespace ssl = boost::asio::ssl;
using tcp = net::ip::tcp;
using json = nlohmann::json;

void run_websocket() {
    try {
        std::string host = "ws.gomarket-cpp.goquant.io";
        std::string port = "443";
        std::string target = "/ws/l2-orderbook/okx/BTC-USDT-SWAP";

        net::io_context ioc;
        ssl::context ctx{ssl::context::tlsv12_client};

        websocket::stream<beast::ssl_stream<tcp::socket>> ws{ioc, ctx};

        tcp::resolver resolver{ioc};
        auto const results = resolver.resolve(host, port);
        net::connect(ws.next_layer().next_layer(), results.begin(), results.end());

        ws.next_layer().handshake(ssl::stream_base::client);
        ws.handshake(host, target);

        std::cout << "Connected to WebSocket!" << std::endl;

        std::vector<double> recent_prices;
        const size_t max_prices = 50; // adjust window size

        while (true) {
            beast::flat_buffer buffer;
            ws.read(buffer);
            std::string message = beast::buffers_to_string(buffer.data());

            json j = json::parse(message, nullptr, false);
            if (j.is_discarded()) {
                std::cerr << "Invalid JSON received." << std::endl;
                continue;
            }

            if (!j.contains("asks") || !j.contains("bids")) {
                std::cerr << "Unexpected JSON structure: " << j.dump() << std::endl;
                continue;
            }

            OrderBook ob;

            for (const auto& ask : j["asks"]) {
                if (ask.size() >= 2)
                    ob.asks.emplace_back(OrderLevel{ std::stod(ask[0].get<std::string>()), std::stod(ask[1].get<std::string>()) });
            }

            for (const auto& bid : j["bids"]) {
                if (bid.size() >= 2)
                    ob.bids.emplace_back(OrderLevel{ std::stod(bid[0].get<std::string>()), std::stod(bid[1].get<std::string>()) });
            }

            if (!ob.asks.empty() && !ob.bids.empty()) {
                std::cout << "\n----------------------" << std::endl;
                std::cout << "Top Ask: " << ob.asks.front().price << " Qty: " << ob.asks.front().quantity << std::endl;
                std::cout << "Top Bid: " << ob.bids.front().price << " Qty: " << ob.bids.front().quantity << std::endl;

                // === ANALYSIS SECTION ===
                double usd_amount = 100.0;
                OrderSide side = OrderSide::BUY;  // example: simulate market buy
                const std::string exchange = "OKX";

                // Update price history
                double mid_price = (ob.asks.front().price + ob.bids.front().price) / 2.0;
                recent_prices.push_back(mid_price);
                if (recent_prices.size() > max_prices)
                    recent_prices.erase(recent_prices.begin());

                // Dummy values (replace later with actual data if available)
                MarketImpactParams mi_params = {0.0001, 0.00003};
                FeeTier tier = FeeTier::TIER1;
                MakerTakerInput mk_input = {
                    true,     // is_market_order
                    0.6,      // volatility (dummy)
                    0.4,      // order book depth (dummy)
                    0.3       // time since last trade (dummy)
                };

                // Call the analyzer
                TradeAnalyzer analyzer(ob, exchange, tier);
                TradeCostResult result = analyzer.analyze(ob, usd_amount, tier, mi_params, mk_input, recent_prices, exchange);

                std::cout << "Expected Slippage: " << result.slippage << " %" << std::endl;
                std::cout << "Fee: $" << result.fee << std::endl;
                std::cout << "Market Impact: $" << result.market_impact << std::endl;
                std::cout << "Net Cost: $" << result.net_cost << std::endl;
                std::cout << "Maker Probability: " << result.maker_taker_result.maker_prob << std::endl;
                std::cout << "Taker Probability: " << result.maker_taker_result.taker_prob << std::endl;

            }
        }
    } catch (const std::exception& e) {
        std::cerr << "WebSocket error: " << e.what() << std::endl;
    }
}
