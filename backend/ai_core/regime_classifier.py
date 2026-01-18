from __future__ import annotations

import time
from collections import deque
from typing import Deque

from backend.utils.logger import get_logger

logger = get_logger("RegimeClassifier")


class RegimeClassifier:
    """
    Regime classifier with hysteresis:
    - confirmation window
    - minimum hold time
    """

    def __init__(
        self,
        window: int = 20,
        trend_threshold: float = 0.12,
        confirm_ticks: int = 5,
        min_hold_seconds: float = 2.0,
    ):
        self.window = window
        self.trend_threshold = trend_threshold
        self.confirm_ticks = confirm_ticks
        self.min_hold_seconds = min_hold_seconds

        self.prices: Deque[float] = deque(maxlen=window)

        self.current_regime: str = "UNKNOWN"
        self._candidate_regime: str | None = None
        self._candidate_count: int = 0
        self._last_switch_ts: float = 0.0

    # -------------------------------------------------

    def update(self, price: float) -> str:
        self.prices.append(price)

        if len(self.prices) < self.window:
            return self.current_regime

        delta = abs(self.prices[-1] - self.prices[0])
        avg_move = delta / max(1, self.window)

        proposed = (
            "TREND" if avg_move >= self.trend_threshold else "CHOP"
        )

        now = time.time()

        # ---- same regime → reset candidate ----
        if proposed == self.current_regime:
            self._candidate_regime = None
            self._candidate_count = 0
            return self.current_regime

        # ---- too soon to switch ----
        if now - self._last_switch_ts < self.min_hold_seconds:
            return self.current_regime

        # ---- candidate tracking ----
        if proposed != self._candidate_regime:
            self._candidate_regime = proposed
            self._candidate_count = 1
        else:
            self._candidate_count += 1

        if self._candidate_count >= self.confirm_ticks:
            logger.info(
                f"[REGIME] Switching {self.current_regime} → {proposed}"
            )
            self.current_regime = proposed
            self._candidate_regime = None
            self._candidate_count = 0
            self._last_switch_ts = now

        return self.current_regime
