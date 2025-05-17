#ifndef ORDERBOOK_HPP
#define ORDERBOOK_HPP

#include <vector>

struct OrderLevel {
    double price;
    double quantity;
};

struct OrderBook {
    std::vector<OrderLevel> asks;
    std::vector<OrderLevel> bids;
};

#endif // ORDERBOOK_HPP
