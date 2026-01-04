# File: backend/ai_core/paper_trader.py
from __future__ import annotations

import random
from typing import Dict

from backend.utils.event_log import log_event


class PaperTrader:
    """
    Deterministic-enough paper trader used by LiveTrader.
    Returns pnl (float) every step.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def execute(self, action: str, size: float, price: float) -> float:
        if action == "buy":
            pnl = self.rng.gauss(size * 0.01, size * 0.005)
        elif action == "sell":
            pnl = self.rng.gauss(-size * 0.008, size * 0.005)
        else:
            pnl = 0.0

        log_event(
            "paper.trade",
            action=action,
            size=round(size, 4),
            price=round(price, 4),
            pnl=round(pnl, 4),
        )
        return float(pnl)
