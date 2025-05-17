import asyncio
import sys
from PyQt6.QtCore import QCoreApplication, QThread
from core.websocket_client import WebSocketWorker

def print_result(result):
    print("Received WebSocket Result:")
    for key, value in result.items():
        print(f"  {key} {value}")
    print("-" * 40)

if __name__ == "__main__":
    worker = WebSocketWorker(
        host="ws.gomarket-cpp.goquant.io",
        port="443",
        target="/ws/l2-orderbook/okx/BTC-USDT-SWAP"
    )
    asyncio.run(worker.run())