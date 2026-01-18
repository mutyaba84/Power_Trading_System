from __future__ import annotations

from typing import Dict, Any
from backend.utils.logger import get_logger

logger = get_logger("RegimeMemory")


class RegimeMemory:
    """
    Isolates learning per regime.
    """

    def __init__(self):
        self.buffers: Dict[str, list[Dict[str, Any]]] = {
            "TREND": [],
            "CHOP": [],
            "HIGH_VOL": [],
        }

    def store(self, regime: str, experience: Dict[str, Any]) -> None:
        if regime not in self.buffers:
            regime = "CHOP"

        self.buffers[regime].append(experience)

    def get(self, regime: str):
        return self.buffers.get(regime, [])
