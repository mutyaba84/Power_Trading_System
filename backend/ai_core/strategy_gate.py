from __future__ import annotations


class StrategyGate:
    """
    Single source of truth for which strategy is valid in which regime.
    """

    def __init__(self):
        self.allowed_map = {
            "CHOP": {"mean_reversion"},
            "TREND": {"momentum"},
        }

    def allowed(self, strategy: str, regime: str) -> bool:
        strategy = (strategy or "").lower()
        regime = (regime or "").upper()

        if regime not in self.allowed_map:
            return False

        return strategy in self.allowed_map[regime]
