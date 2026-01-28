from __future__ import annotations
import time
from typing import Dict, Any

from backend.brokers.alpaca_broker import AlpacaBroker



class AlpacaMarketFeed:
    def __init__(self, broker: AlpacaBroker, symbol: str = "SPY"):
        self.broker = broker
        self.symbol = symbol

    def get_tick(self) -> Dict[str, Any]:
        bars = self.broker.get_bars(
            symbol=self.symbol,
            timeframe="1Min",
            limit=2,
        )

        if not bars or len(bars) < 2:
            return {}

        last = bars[-1]
        prev = bars[-2]

        price = float(last.c)
        volatility = abs(last.c - prev.c) / prev.c

        return {
            "symbol": self.symbol,
            "price": price,
            "volatility": volatility,
            "confidence": 0.5,
            "timestamp": time.time(),
        }
    

class AlpacaDataFeed:
    def __init__(self, symbol: str, timeframe: str):
        self.broker = AlpacaBroker()
        self.symbol = symbol
        self.timeframe = timeframe

    def next_tick(self):
        bar = self.broker.get_latest_bar(self.symbol, self.timeframe)
        if not bar:
            return None
        return {
            "price": float(bar["close"]),
            "timestamp": bar["timestamp"],
        }
