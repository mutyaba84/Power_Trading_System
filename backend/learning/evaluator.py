# backend/learning/evaluator.py
from __future__ import annotations


def approve(candidate: dict, baseline: dict) -> bool:
    """
    Approve only if risk-adjusted improvement exists.
    """

    if not candidate:
        return False

    if candidate["expected_pnl"] <= baseline.get("expected_pnl", 0):
        return False

    if candidate["pnl_volatility"] > baseline.get("pnl_volatility", float("inf")):
        return False

    return True
