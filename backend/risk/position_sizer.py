# backend/risk/position_sizer.py
from __future__ import annotations

from typing import Optional


class PositionSizer:
    """
    Confidence & volatility based position sizing.
    Produces a SAFE, bounded position size.
    """

    def __init__(
        self,
        base_size: float,
        min_size: float,
        max_size: float,
        min_confidence: float = 0.1,
        max_confidence: float = 1.0,
        target_volatility: float = 0.01,
    ):
        self.base_size = base_size
        self.min_size = min_size
        self.max_size = max_size
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.target_volatility = target_volatility

    # ------------------------------------------------------------

    def size(
        self,
        *,
        confidence: Optional[float],
        volatility: Optional[float],
    ) -> float:
        """
        Compute position size.
        """

        # Safety defaults
        if confidence is None or volatility is None:
            return 0.0

        # Clamp confidence
        conf = max(self.min_confidence, min(confidence, self.max_confidence))

        # Volatility adjustment (inverse)
        vol_factor = self.target_volatility / max(volatility, 1e-6)

        # Raw size
        raw_size = self.base_size * conf * vol_factor

        # Clamp final size
        final_size = max(self.min_size, min(raw_size, self.max_size))

        return float(final_size)
