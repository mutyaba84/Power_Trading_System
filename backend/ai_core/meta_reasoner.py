# File: backend/ai_core/meta_reasoner.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .episodic_memory import EpisodicMemory


class MetaReasoner:
    """
    Lightweight reasoning over recent episodes.
    Produces a small 'insight' dict the controller can log.
    """

    def __init__(self, memory: Optional[EpisodicMemory] = None) -> None:
        self.memory = memory or EpisodicMemory()

    def analyze(self, n: int = 20) -> Dict[str, Any]:
        episodes = self.memory.load_recent(n)
        if not episodes:
            return {"insight": "No episodes yet", "avg_pnl": 0.0, "n": 0}

        # Episodes can be stored as list[trade_event] or dict; normalize
        pnls: List[float] = []

        for ep in episodes:
            if isinstance(ep, list):
                for step in ep:
                    if isinstance(step, dict) and "pnl" in step:
                        try:
                            pnls.append(float(step["pnl"]))
                        except Exception:
                            pass
            elif isinstance(ep, dict):
                if "pnl" in ep:
                    try:
                        pnls.append(float(ep["pnl"]))
                    except Exception:
                        pass

        if not pnls:
            return {"insight": "Episodes found but no pnl fields", "avg_pnl": 0.0, "n": len(episodes)}

        avg_pnl = sum(pnls) / max(1, len(pnls))
        insight = f"Avg pnl over last {min(n, len(episodes))} episodes: {avg_pnl:.2f}"
        return {"insight": insight, "avg_pnl": round(avg_pnl, 4), "n": len(episodes)}
