from __future__ import annotations

import os
import time
from typing import Dict, Any

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest


class AlpacaFeed:
    """
    Simple polling feed for latest quote data.
    Returns a controller-friendly tick dict:
    {
        "symbol": "SPY",
        "price": 123.45,
        "timestamp": 1710000000.0,
        "confidence": 0.5,
    }
    """

    def __init__(self, api_key: str, secret_key: str, symbol: str = "SPY"):
        self.symbol = symbol
        self.client = StockHistoricalDataClient(api_key, secret_key)

    def next_tick(self) -> Dict[str, Any]:
        req = StockLatestQuoteRequest(symbol_or_symbols=self.symbol)
        quote_map = self.client.get_stock_latest_quote(req)

        quote = quote_map[self.symbol]

        bid = float(quote.bid_price or 0.0)
        ask = float(quote.ask_price or 0.0)

        if bid > 0 and ask > 0:
            price = (bid + ask) / 2.0
        elif ask > 0:
            price = ask
        else:
            price = bid

        return {
            "symbol": self.symbol,
            "price": price,
            "timestamp": time.time(),
            "confidence": 0.5,
        }