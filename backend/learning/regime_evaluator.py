# backend/learning/regime_evaluator.py
from __future__ import annotations


def approve_regime(
    *,
    candidate: dict,
    baseline: dict,
) -> bool:
    if candidate["expected_pnl"] <= baseline.get("expected_pnl", 0):
        return False

    if candidate["pnl_volatility"] > baseline.get("pnl_volatility", float("inf")):
        return False

    return True
