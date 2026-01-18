# backend/learning/dataset_builder.py
from __future__ import annotations

from typing import List, Tuple
import numpy as np


def build_dataset(snapshots: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert snapshots to (X, y).
    """

    X = []
    y = []

    for s in snapshots:
        f = s.get("features", {})
        X.append([
            f.get("volatility", 0.0),
            f.get("confidence", 0.0),
            f.get("trend_strength", 0.0),
        ])
        y.append(s.get("pnl", 0.0))

    return np.array(X, dtype=float), np.array(y, dtype=float)
