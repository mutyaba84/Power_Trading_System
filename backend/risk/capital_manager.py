# backend/risk/capital_manager.py
from __future__ import annotations

from typing import Optional


class CapitalManager:
    """
    Controls global capital aggressiveness.
    Produces a capital multiplier in [min_scale, max_scale].
    """

    def __init__(
        self,
        min_scale: float = 0.25,
        max_scale: float = 1.5,
        drawdown_sensitivity: float = 2.0,
        recovery_rate: float = 0.05,
    ):
        
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.drawdown_sensitivity = drawdown_sensitivity
        self.recovery_rate = recovery_rate

        self._peak_equity: Optional[float] = None
        self._scale: float = 1.0

    # ------------------------------------------------------------

    def update(self, *, equity: float) -> None:
        """
        Update capital scaling based on current equity.
        Call once per tick or trade.
        """

        if self._peak_equity is None:
            self._peak_equity = equity
            self._scale = 1.0
            return

        # Update peak
        if equity > self._peak_equity:
            self._peak_equity = equity
            # Slow recovery
            self._scale = min(
                self.max_scale,
                self._scale + self.recovery_rate,
            )
            return

        # Drawdown-based reduction
        drawdown = (self._peak_equity - equity) / self._peak_equity

        reduction = drawdown * self.drawdown_sensitivity
        self._scale = max(
            self.min_scale,
            1.0 - reduction,
        )

    # ------------------------------------------------------------

    def scale(self) -> float:
        """
        Return current capital multiplier.
        """
        return float(max(self.min_scale, min(self._scale, self.max_scale)))
