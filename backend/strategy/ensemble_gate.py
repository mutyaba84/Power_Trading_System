# backend/strategy/ensemble_gate.py
from __future__ import annotations

from typing import Dict, Optional


class StrategyGate:
    """
    Regime-based strategy gating.
    Determines which strategy is allowed to act.
    """

    def __init__(
        self,
        trend_threshold: float = 0.6,
        range_threshold: float = 0.4,
        max_active: int = 1,
    ):
        self.trend_threshold = trend_threshold
        self.range_threshold = range_threshold
        self.max_active = max_active

    # ------------------------------------------------------------

    def select(
        self,
        *,
        strategies: Dict[str, Dict],
        regime: Optional[str],
    ) -> Dict[str, Dict]:
        """
        Returns subset of strategies allowed to act.

        strategies example:
        {
            "momentum": {"score": 0.8},
            "mean_reversion": {"score": 0.3},
        }
        """

        if not strategies:
            return {}

        allowed: Dict[str, Dict] = {}

        # --- Regime-based gating
        for name, meta in strategies.items():
            score = meta.get("score", 0.0)

            if regime == "trend" and score >= self.trend_threshold:
                allowed[name] = meta

            elif regime == "range" and score <= self.range_threshold:
                allowed[name] = meta

            elif regime is None:
                allowed[name] = meta  # fallback

        # --- Limit active strategies
        if len(allowed) > self.max_active:
            allowed = dict(
                sorted(
                    allowed.items(),
                    key=lambda x: x[1].get("score", 0.0),
                    reverse=True,
                )[: self.max_active]
            )

        return allowed
