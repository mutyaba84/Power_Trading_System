# backend/learning/confidence_calibrator.py
from __future__ import annotations

import numpy as np
from typing import Dict


class ConfidenceCalibrator:
    """
    Empirical confidence calibration.
    """

    def fit(self, data: Dict) -> Dict:
        if not data:
            return {}

        bins = data["bins"]
        rates = data["empirical_rates"]

        # Smooth slightly to avoid noise
        smooth = np.convolve(rates, [0.25, 0.5, 0.25], mode="same")

        return {
            "bins": bins.tolist(),
            "calibrated_rates": smooth.tolist(),
        }
