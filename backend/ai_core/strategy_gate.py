from __future__ import annotations
from typing import Dict


class StrategyGate:
    """
    Defines which strategies are allowed per regime
    and how strongly they are weighted.
    Weight = 0.0 means blocked.
    """

    def __init__(self):
        self.matrix: Dict[str, Dict[str, float]] = {
            "TREND": {
                "momentum": 1.0,
                "breakout": 0.5,
                "mean_reversion": 0.0,
            },
            "CHOP": {
                "momentum": 0.0,
                "breakout": 0.0,
                "mean_reversion": 1.0,
            },
            "UNKNOWN": {
                "momentum": 0.0,
                "breakout": 0.0,
                "mean_reversion": 0.0,
            },
        }

    def weight(self, *, strategy: str, regime: str) -> float:
        return self.matrix.get(regime, {}).get(strategy, 0.0)

    def allowed(self, *, strategy: str, regime: str) -> bool:
        return self.weight(strategy=strategy, regime=regime) > 0.0
