import asyncio
import json
import ssl
from collections import deque
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from core.trade_analyzer import TradeAnalyzer, OrderBook, OrderLevel, MarketImpactParams, FeeTier, MakerTakerInput


class WebSocketWorker(QObject):
    result_signal = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, host, port, target, usd_amount=100.0, fee_tier=FeeTier.TIER1, volatility=0.6):
        super().__init__()
        self.host = host
        self.port = port
        self.target = target
        self.usd_amount = usd_amount
        self.fee_tier = fee_tier
        self.volatility = volatility
        self.recent_prices = deque(maxlen=50)
        self._running = True

    def set_parameters(self, usd_amount=None, fee_tier=None, volatility=None):
        """Update parameters from the UI."""
        if usd_amount is not None:
            self.usd_amount = usd_amount
        if fee_tier is not None:
            self.fee_tier = fee_tier
        if volatility is not None:
            self.volatility = volatility

    async def connect(self):
        import websockets
        uri = f"wss://{self.host}:{self.port}{self.target}"
        ssl_context = ssl.create_default_context()

        last_message_time = None  # for measuring stream latency

        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            while self._running:
                try:
                    message = await websocket.recv()
                    current_time = time.perf_counter()

                    # Measure stream data latency
                    if last_message_time is not None:
                        stream_latency_ms = (current_time - last_message_time) * 1000
                    else:
                        stream_latency_ms = 0.0  # first message, no latency to compare

                    last_message_time = current_time

                    start_process = time.perf_counter()  # start timing data processing
                    data = json.loads(message)

                    if 'asks' not in data or 'bids' not in data:
                        continue

                    order_book = OrderBook()
                    for ask in data['asks']:
                        if len(ask) >= 2:
                            price = float(ask[0])
                            quantity = float(ask[1])
                            order_book.asks.append(OrderLevel(price, quantity))
                    for bid in data['bids']:
                        if len(bid) >= 2:
                            price = float(bid[0])
                            quantity = float(bid[1])
                            order_book.bids.append(OrderLevel(price, quantity))

                    if order_book.asks and order_book.bids:
                        top_ask = order_book.asks[0]
                        top_bid = order_book.bids[0]
                        mid_price = (top_ask.price + top_bid.price) / 2.0
                        self.recent_prices.append(mid_price)

                        mk_input = MakerTakerInput(
                            is_market_order=True,
                            volatility=self.volatility,
                            order_book_depth=0.4,
                            time_since_last_trade=0.3
                        )

                        analyzer = TradeAnalyzer(order_book, exchange_name="OKX", fee_tier=self.fee_tier)

                        spread = analyzer.compute_spread()
                        sigma = analyzer.compute_volatility(self.recent_prices)

                        # Estimate eta, gamma, lambda based on live data
                        eta = 0.0001 + 0.05 * spread         # Temporary market impact scaling with spread
                        gamma = eta * 0.25                   # Permanent market impact scaled from eta
                        lambda_ = 0.05 + 0.1 * sigma         # Risk aversion scaled from volatility

                        mi_params = MarketImpactParams(
                            eta=eta,
                            gamma=gamma,
                            lambda_=lambda_,
                            sigma=sigma,
                            alpha=1.0,  # Can tune these further if you want power-law style
                            beta=1.0
                        )
                        result = analyzer.analyze(
                            order_book,
                            self.usd_amount,
                            self.fee_tier,
                            mi_params,
                            mk_input,
                            list(self.recent_prices),
                            "OKX"
                        )

                        end_process = time.perf_counter()
                        processing_latency_ms = (end_process - start_process) * 1000

                        print(f"[Stream Data Latency] {stream_latency_ms:.3f} ms")
                        print(f"[Data Processing Latency] {processing_latency_ms:.3f} ms")
                        print(top_ask, top_bid)

                        self.result_signal.emit({
                            "top_ask": top_ask,
                            "top_bid": top_bid,
                            "slippage": result.slippage,
                            "fee": result.fee,
                            "impact": result.market_impact,
                            "net_cost": result.net_cost,
                            "maker_prob": result.maker_taker_result.maker_prob,
                            "taker_prob": result.maker_taker_result.taker_prob,
                            "stream_latency_ms": stream_latency_ms,
                            "processing_latency_ms": processing_latency_ms,
                        })

                except Exception as e:
                    print(f"WebSocket error: {e}")
                    break

        self.finished.emit()

    def run(self):
        asyncio.run(self.connect())

    def stop(self):
        self._running = False
