from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.utils.event_log import log_event
from backend.utils.logger import get_logger

logger = get_logger("DataFeed")


@dataclass
class FeedConfig:
    symbol: str = "POWER"
    start_price: float = 100.0
    drift: float = 0.0          # mean drift per tick
    volatility: float = 0.6     # std-dev of price change per tick
    seed: Optional[int] = None  # deterministic run if set


class DataFeed:
    """
    Lightweight synthetic data feed (no pandas).

    Emits ticks like:
      {
        "symbol": "POWER",
        "timestamp": 1700000000.123,
        "price": 100.12,
        "seq": 1
      }

    Env overrides:
      - FEED_SYMBOL
      - FEED_START_PRICE
      - FEED_DRIFT
      - FEED_VOLATILITY
      - FEED_SEED
    """

    def __init__(self, config: Optional[FeedConfig] = None) -> None:
        cfg = config or FeedConfig()

        # Allow env overrides
        self.symbol = os.getenv("FEED_SYMBOL", cfg.symbol)

        self.price = float(os.getenv("FEED_START_PRICE", str(cfg.start_price)))
        self.drift = float(os.getenv("FEED_DRIFT", str(cfg.drift)))
        self.volatility = float(os.getenv("FEED_VOLATILITY", str(cfg.volatility)))

        seed_raw = os.getenv("FEED_SEED")
        if seed_raw is not None and seed_raw != "":
            try:
                self.seed = int(seed_raw)
            except Exception:
                self.seed = None
        else:
            self.seed = cfg.seed

        self._rng = random.Random(self.seed)
        self.seq = 0

        logger.info(
            f"DataFeed init symbol={self.symbol} start={self.price} drift={self.drift} vol={self.volatility} seed={self.seed}"
        )

        log_event(
            "feed.init",
            symbol=self.symbol,
            start_price=self.price,
            drift=self.drift,
            volatility=self.volatility,
            seed=self.seed,
        )

    def next_tick(self) -> Dict[str, Any]:
        """
        Generate next synthetic tick.
        """
        self.seq += 1

        # Gaussian step around drift
        step = self._rng.gauss(self.drift, self.volatility)
        self.price = max(0.01, float(self.price + step))

        tick = {
            "symbol": self.symbol,
            "timestamp": time.time(),
            "price": round(self.price, 4),
            "seq": self.seq,
        }

        # Optional: keep feed logging low-volume (comment out if noisy)
        # log_event("feed.tick", **tick)

        return tick

    def reset(self, start_price: Optional[float] = None, seed: Optional[int] = None) -> None:
        """
        Reset feed state for reproducible tests.
        """
        if start_price is not None:
            self.price = float(start_price)

        if seed is not None:
            self.seed = int(seed)
            self._rng = random.Random(self.seed)

        self.seq = 0
        log_event("feed.reset", start_price=self.price, seed=self.seed)
