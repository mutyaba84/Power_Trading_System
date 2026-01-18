# backend/learning/regime_learner.py
from __future__ import annotations

from typing import Dict
import numpy as np


class RegimeLearner:
    """
    Learns parameters per regime.
    """

    def fit(self, datasets: Dict[str, tuple]) -> Dict[str, Dict]:
        proposals: Dict[str, Dict] = {}

        for regime, (X, y) in datasets.items():
            if len(y) < 30:
                continue

            avg_pnl = float(np.mean(y))
            pnl_std = float(np.std(y))

            # Conservative parameter adjustments
            conf_threshold = 0.25 if avg_pnl > 0 else 0.35

            proposals[regime] = {
                "confidence_threshold": conf_threshold,
                "expected_pnl": avg_pnl,
                "pnl_volatility": pnl_std,
            }

        return proposals
