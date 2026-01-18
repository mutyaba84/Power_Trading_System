# backend/learning/mirror_analysis.py
from __future__ import annotations

from typing import Dict, List
import numpy as np


def analyze_divergence(
    sim: List[dict],
    paper: List[dict],
) -> Dict[str, float]:
    """
    Compare simulation vs paper performance.
    """

    def stats(snaps):
        if not snaps:
            return 0.0, 0.0
        pnls = [s["pnl"] for s in snaps if s.get("pnl") is not None]
        return float(np.mean(pnls)), float(np.std(pnls))

    sim_mean, sim_std = stats(sim)
    paper_mean, paper_std = stats(paper)

    divergence = sim_mean - paper_mean

    penalty = 1.0
    if divergence > 0:
        penalty = max(0.5, 1.0 - divergence / (abs(sim_mean) + 1e-6))

    return {
        "sim_mean": sim_mean,
        "paper_mean": paper_mean,
        "divergence": divergence,
        "confidence_penalty": penalty,
    }
