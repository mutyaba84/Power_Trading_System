from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from backend.utils.logger import get_logger

logger = get_logger("AlpacaLiveFeed")


class AlpacaLiveFeed:
    """
    Simple live feed adapter for Alpaca.

    This version is polling-based and intentionally minimal:
    - returns one tick at a time
    - uses latest trade/quote/bar if available
    - falls back safely without crashing the controller

    Expected output:
        {
            "symbol": "SPY",
            "price": 512.34,
            "timestamp": 1710446400.0,
            "source": "alpaca"
        }
    """

    def __init__(self, symbol: Optional[str] = None):
        self.symbol = symbol or os.getenv("ALPACA_SYMBOL", "SPY")
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        self.paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"

        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca API keys are missing")

        self._client = None
        self._last_price: Optional[float] = None

        logger.info(f"AlpacaLiveFeed initialized for {self.symbol}")

    def _get_client(self):
        if self._client is not None:
            return self._client

        # Prefer the modern Alpaca SDK
        try:
            from alpaca.data.historical import StockHistoricalDataClient

            self._client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
            )
            return self._client
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Alpaca data client: {e}") from e

    def next_tick(self) -> Optional[Dict[str, Any]]:
        """
        Poll Alpaca for the latest minute bar and return a normalized tick dict.
        """
        client = self._get_client()

        try:
            from alpaca.data.requests import StockLatestBarRequest

            request = StockLatestBarRequest(symbol_or_symbols=[self.symbol])
            bars = client.get_stock_latest_bar(request)

            bar = bars.get(self.symbol)
            if not bar:
                return None

            price = float(bar.close)
            ts = bar.timestamp.timestamp() if getattr(bar, "timestamp", None) else time.time()

            # suppress exact duplicates
            if self._last_price is not None and price == self._last_price:
                return {
                    "symbol": self.symbol,
                    "price": price,
                    "timestamp": ts,
                    "source": "alpaca",
                }

            self._last_price = price

            return {
                "symbol": self.symbol,
                "price": price,
                "timestamp": ts,
                "source": "alpaca",
            }

        except Exception as e:
            logger.warning(f"[ALPACA FEED] next_tick failed: {e}")
            return None
