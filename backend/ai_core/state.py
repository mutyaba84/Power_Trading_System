# backend/app/state.py

from typing import List, Dict, Any

from backend.core import state

class TradingState:
    def __init__(self):
        self.trades: List[Dict[str, Any]] = []
        self.last_decision: Dict[str, Any] | None = None
        self.last_sentiment: Dict[str, Any] | None = None
        self.equity: float = 10000.0
        self.running: bool = False

        state["total_equity"] = 0.0
        state["deploy_pct"] = 0.25   # 🔥 key setting
        state["deployable_equity"] = 0.0

STATE = TradingState()
