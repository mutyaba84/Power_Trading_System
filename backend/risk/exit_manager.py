# backend/risk/exit_manager.py
from __future__ import annotations

import time
from typing import Optional


class ExitManager:
    """
    Deterministic exit logic for open trades.
    """

    def __init__(
        self,
        max_hold_seconds: int = 30,
        max_adverse_vols: float = 2.0,
        profit_decay_ratio: float = 0.5,
    ):
        self.max_hold_seconds = max_hold_seconds
        self.max_adverse_vols = max_adverse_vols
        self.profit_decay_ratio = profit_decay_ratio

    # ------------------------------------------------------------

    def should_exit(
        self,
        *,
        entry_price: float,
        current_price: float,
        entry_ts: float,
        peak_price: float,
        side: str,
        volatility: Optional[float],
        now_ts: Optional[float] = None,
    ) -> bool:
        """
        Returns True if trade should be exited.
        """

        now = now_ts or time.time()

        # --- Time-based exit
        if (now - entry_ts) > self.max_hold_seconds:
            return True

        if volatility is None:
            return False

        # --- Adverse volatility stop
        adverse_move = (
            (entry_price - current_price)
            if side == "buy"
            else (current_price - entry_price)
        )

        if adverse_move > self.max_adverse_vols * volatility * entry_price:
            return True

        # --- Profit decay exit
        favorable_move = (
            (peak_price - entry_price)
            if side == "buy"
            else (entry_price - peak_price)
        )

        current_gain = (
            (current_price - entry_price)
            if side == "buy"
            else (entry_price - current_price)
        )

        if favorable_move > 0:
            if current_gain < favorable_move * self.profit_decay_ratio:
                return True

        return False
