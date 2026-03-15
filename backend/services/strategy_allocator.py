from __future__ import annotations


class StrategyAllocator:
    """
    Deterministic regime -> strategy mapping.

    This keeps the architecture simple and avoids conflicts between:
    - regime classifier
    - allocator
    - gate
    """

    def __init__(self, strategy_tracker=None):
        self.strategy_tracker = strategy_tracker

    def choose(self, regime: str) -> str:
        regime = (regime or "").upper()

        if regime == "CHOP":
            return "mean_reversion"

        if regime == "TREND":
            return "momentum"

        return "none"
