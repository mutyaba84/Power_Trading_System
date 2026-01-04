# File: backend/ai_core/adaptive_execution_engine.py
from __future__ import annotations

import random
import time
import json
from pathlib import Path
from typing import Any, Dict

from backend.utils.paths import storage_root


class AdaptiveExecutionEngine:
    def __init__(self, max_risk: float = 0.05):
        self.memory_root = storage_root()
        self.exec_dir = self.memory_root / "executions"
        self.exec_dir.mkdir(parents=True, exist_ok=True)

        self.max_risk = float(max_risk)
        self.current_equity = 100000.0  # demo initial equity

    def _get_dynamic_position_size(self, confidence: float, volatility: float) -> float:
        base_size = self.current_equity * self.max_risk
        adj = confidence / (1.0 + volatility)
        return round(base_size * adj, 2)

    def _select_order_type(self, confidence: float, volatility: float) -> str:
        if confidence > 0.8 and volatility < 0.02:
            return "market"
        if 0.5 < confidence <= 0.8:
            return "limit"
        return "conditional"

    def execute(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        confidence = abs(float(strategy.get("expected_avg_pnl", 0.0))) / 10.0
        confidence = max(0.0, min(1.0, confidence))

        volatility = random.uniform(0.005, 0.03)
        order_type = self._select_order_type(confidence, volatility)
        size = self._get_dynamic_position_size(confidence, volatility)

        direction = strategy.get("recommended_action", "hold")
        if direction == "buy":
            pnl = random.gauss(size * 0.01, size * 0.005)
        elif direction == "sell":
            pnl = random.gauss(size * -0.008, size * 0.005)
        else:
            pnl = 0.0

        self.current_equity += pnl

        result = {
            "timestamp": time.time(),
            "direction": direction,
            "order_type": order_type,
            "size": size,
            "volatility": round(volatility, 4),
            "confidence": round(confidence, 4),
            "pnl": round(pnl, 2),
            "equity": round(self.current_equity, 2),
        }

        filename = self.exec_dir / f"exec_{int(time.time()*1000)}.json"
        filename.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
