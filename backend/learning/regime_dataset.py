# backend/learning/regime_dataset.py
from __future__ import annotations

from typing import Dict, List, Tuple
import numpy as np


def split_by_regime(
    snapshots: List[dict],
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Returns datasets per regime.
    """

    buckets: Dict[str, List[dict]] = {
        "trend": [],
        "range": [],
        "high_vol": [],
    }

    for s in snapshots:
        regime = s.get("regime")
        if regime in buckets:
            buckets[regime].append(s)

    datasets: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    for regime, snaps in buckets.items():
        if len(snaps) < 30:
            continue

        X = []
        y = []

        for s in snaps:
            f = s.get("features", {})
            X.append([
                f.get("volatility", 0.0),
                f.get("confidence", 0.0),
                f.get("trend_strength", 0.0),
            ])
            y.append(s.get("pnl", 0.0))

        datasets[regime] = (
            np.array(X, dtype=float),
            np.array(y, dtype=float),
        )

    return datasets
