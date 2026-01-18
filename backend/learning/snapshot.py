# backend/learning/snapshot.py
from __future__ import annotations

from typing import Dict, Any
import time


def learning_snapshot(
    *,
    features: Dict[str, Any],
    action: str,
    confidence: float,
    pnl: float,
    equity: float,
    regime: str | None,
) -> Dict[str, Any]:
    """
    Immutable learning snapshot.
    Safe to log.
    """
    return {
        "ts": time.time(),
        "features": features,
        "action": action,
        "confidence": confidence,
        "pnl": pnl,
        "equity": equity,
        "regime": regime,
    }
