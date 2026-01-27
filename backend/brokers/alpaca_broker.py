# backend/brokers/alpaca_broker.py

import os
from typing import List

from alpaca_trade_api import REST
from backend.utils.logger import get_logger

logger = get_logger("AlpacaBroker")


class AlpacaBroker:
    def __init__(self, mode: str = "paper"):
        self.mode = mode
        self.client: REST | None = None

    def connect(self):
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")

        if not api_key or not secret_key:
            raise RuntimeError("Alpaca API keys missing")

        base_url = (
            "https://paper-api.alpaca.markets"
            if self.mode != "live"
            else "https://api.alpaca.markets"
        )

        self.client = REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url=base_url,
        )

        logger.info(f"[ALPACA] Connected ({self.mode.upper()})")

    # -------------------------------------------------
    # MARKET DATA
    # -------------------------------------------------

    def get_latest_price(self, symbol: str) -> float:
        assert self.client is not None, "Broker not connected"

        bar = self.client.get_latest_bar(symbol)
        price = float(bar.c)

        logger.debug(f"[ALPACA DATA] {symbol} price={price}")
        return price

    def next_tick(self, symbol: str = "SPY") -> dict:
        """
        Unified interface so controller can treat Alpaca like DataFeed
        """
        price = self.get_latest_price(symbol)

        return {
            "symbol": symbol,
            "price": price,
        }

    # -------------------------------------------------
    # EXECUTION
    # -------------------------------------------------

    def place_order(
        self,
        *,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
    ):
        assert self.client is not None, "Broker not connected"

        logger.info(
            f"[ALPACA ORDER] {side.upper()} {qty:.2f} {symbol}"
        )

        self.client.submit_order(
            symbol=symbol,
            qty=round(qty, 2),
            side=side,
            type=order_type,
            time_in_force="day",
        )
