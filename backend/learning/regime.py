# backend/learning/regime.py
from __future__ import annotations

from typing import Optional


def classify_regime(
    *,
    volatility: float,
    trend_strength: float,
) -> Optional[str]:
    """
    Simple, deterministic regime classifier.
    """

    if volatility > 0.03:
        return "high_vol"

    if trend_strength > 0.6:
        return "trend"

    if trend_strength < 0.3:
        return "range"

    return None
