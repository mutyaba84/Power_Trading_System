# backend/risk/trade_filter.py
from __future__ import annotations

import time
from typing import Optional


class TradeFilter:
    """
    Deterministic trade filter.
    Returns False to BLOCK a trade.
    """

    def __init__(
        self,
        min_volatility: float = 0.001,
        max_volatility: float = 0.05,
        min_seconds_between_trades: int = 2,
        trading_hours: Optional[tuple[int, int]] = None,
    ):
        self.min_volatility = min_volatility
        self.max_volatility = max_volatility
        self.min_seconds_between_trades = min_seconds_between_trades
        self.trading_hours = trading_hours  # e.g. (13, 20) UTC

        self._last_trade_ts: Optional[float] = None

    # ------------------------------------------------------------

    def allow(
        self,
        *,
        volatility: Optional[float],
        now_ts: Optional[float] = None,
    ) -> bool:
        """
        Returns True if trading is allowed.
        """

        now = now_ts or time.time()

        # --- Volatility floor
        if volatility is None:
            return False

        if volatility < self.min_volatility:
            return False

        # --- Volatility ceiling
        if volatility > self.max_volatility:
            return False

        # --- Cooldown
        if self._last_trade_ts is not None:
            if (now - self._last_trade_ts) < self.min_seconds_between_trades:
                return False

        # --- Time-of-day gate
        if self.trading_hours is not None:
            hour = time.gmtime(now).tm_hour
            start, end = self.trading_hours
            if not (start <= hour < end):
                return False

        return True

    # ------------------------------------------------------------

    def notify_trade(self, ts: Optional[float] = None) -> None:
        """
        Call this AFTER a trade is executed.
        """
        self._last_trade_ts = ts or time.time()
