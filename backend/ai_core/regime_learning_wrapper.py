from __future__ import annotations
from typing import Any


class RegimeLearningWrapper:
    """
    Hard-separates learning memory by market regime.
    """

    def __init__(self, engine):
        self.engine = engine

    def reinforce(
        self,
        *,
        strategy: str,
        regime: str,
        reward: float,
        context: str | None = None,
    ):
        key = f"{strategy}|{regime}"
        ctx = context or f"regime={regime}"

        self.engine.reinforce(key, reward, ctx)
