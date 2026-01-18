# backend/learning/learner.py
from __future__ import annotations

import numpy as np
from typing import Dict


class ParameterLearner:
    """
    Learns safe parameter adjustments.
    """

    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Returns proposed parameter updates.
        """

        if len(y) < 50:
            return {}

        avg_pnl = float(np.mean(y))
        pnl_std = float(np.std(y))

        # Simple example: adjust confidence threshold
        new_conf_threshold = 0.3 if avg_pnl < 0 else 0.2

        return {
            "confidence_threshold": new_conf_threshold,
            "expected_pnl": avg_pnl,
            "pnl_volatility": pnl_std,
        }
