# backend/learning/calibration_dataset.py
from __future__ import annotations

from typing import List, Dict
import numpy as np


def build_calibration_data(
    snapshots: List[dict],
    n_bins: int = 10,
) -> Dict[str, np.ndarray]:
    """
    Build empirical confidence calibration data.
    """

    confidences = []
    outcomes = []

    for s in snapshots:
        c = s.get("confidence")
        pnl = s.get("pnl")

        if c is None:
            continue

        confidences.append(float(c))
        outcomes.append(1.0 if pnl > 0 else 0.0)

    if not confidences:
        return {}

    confidences = np.array(confidences)
    outcomes = np.array(outcomes)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(confidences, bins) - 1

    empirical = np.zeros(n_bins)
    counts = np.zeros(n_bins)

    for idx, out in zip(bin_ids, outcomes):
        if 0 <= idx < n_bins:
            empirical[idx] += out
            counts[idx] += 1

    with np.errstate(divide="ignore", invalid="ignore"):
        empirical_rates = np.where(counts > 0, empirical / counts, 0.0)

    return {
        "bins": bins,
        "empirical_rates": empirical_rates,
        "counts": counts,
    }
