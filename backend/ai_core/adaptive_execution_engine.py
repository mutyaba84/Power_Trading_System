import random, json, time
from pathlib import Path
import numpy as np

class AdaptiveExecutionEngine:
    def __init__(self, external_memory="/app/external_memory", max_risk=0.05):
        self.memory_root = Path(external_memory)
        self.exec_dir = self.memory_root / "executions"
        self.exec_dir.mkdir(parents=True, exist_ok=True)
        self.max_risk = max_risk
        self.current_equity = 100000  # demo initial equity

    def _get_dynamic_position_size(self, confidence, volatility):
        """
        Adjust position size dynamically:
        - Higher confidence -> larger position.
        - Higher volatility -> smaller position.
        """
        base_size = self.current_equity * self.max_risk
        adj = confidence / (1 + volatility)
        return round(base_size * adj, 2)

    def _select_order_type(self, confidence, volatility):
        """
        Decide order type:
        - High confidence, low vol => market order
        - Moderate => limit order
        - Low confidence or high vol => conditional / stop order
        """
        if confidence > 0.8 and volatility < 0.02:
            return "market"
        elif 0.5 < confidence <= 0.8:
            return "limit"
        return "conditional"

    def execute(self, strategy):
        """
        Simulate trade execution with adaptive sizing and order control.
        """
        confidence = abs(strategy.get("expected_avg_pnl", 0)) / 10
        volatility = random.uniform(0.005, 0.03)
        order_type = self._select_order_type(confidence, volatility)
        size = self._get_dynamic_position_size(confidence, volatility)

        direction = strategy.get("recommended_action", "hold")
        if direction == "buy":
            pnl = random.gauss(size * 0.01, size * 0.005)
        elif direction == "sell":
            pnl = random.gauss(size * -0.008, size * 0.005)
        else:
            pnl = 0

        self.current_equity += pnl

        result = {
            "timestamp": time.time(),
            "direction": direction,
            "order_type": order_type,
            "size": size,
            "volatility": volatility,
            "confidence": confidence,
            "pnl": round(pnl, 2),
            "equity": round(self.current_equity, 2)
        }

        filename = self.exec_dir / f"exec_{int(time.time())}.json"
        filename.write_text(json.dumps(result, indent=2))
        return result
