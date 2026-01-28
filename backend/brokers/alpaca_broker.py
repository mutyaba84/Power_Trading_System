from __future__ import annotations

import os
import time
from typing import Dict, Optional

from alpaca_trade_api import REST
from backend.utils.logger import get_logger

logger = get_logger("AlpacaBroker")


class AlpacaBroker:
    def __init__(self, symbol: str = "SPY", timeframe: str = "1Min"):
        self.symbol = symbol
        self.timeframe = timeframe

        self.api = REST(
            key_id=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            base_url="https://paper-api.alpaca.markets"
            if os.getenv("ALPACA_PAPER", "true").lower() == "true"
            else "https://api.alpaca.markets",
        )

        self.last_ts: Optional[int] = None
        logger.info(f"[ALPACA] Connected | symbol={symbol} tf={timeframe}")

    def next_tick(self) -> Optional[Dict]:
        try:
            bars = self.api.get_bars(
                self.symbol,
                self.timeframe,
                limit=1,
            )

            if not bars:
                return None

            bar = bars[0]
            ts = int(bar.t.timestamp())

            if self.last_ts and ts <= self.last_ts:
                return None

            self.last_ts = ts

            return {
                "price": float(bar.c),
                "open": float(bar.o),
                "high": float(bar.h),
                "low": float(bar.l),
                "volume": float(bar.v),
                "ts": ts,
                "source": "alpaca",
            }

        except Exception as e:
            logger.error(f"[ALPACA] Data error: {e}")
            time.sleep(1)
            return None
