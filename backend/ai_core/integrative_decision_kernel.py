"""
Integrative Decision Kernel
---------------------------
Final action generator for the Power Trading System.
Merges:
- Cognitive Orchestrator strategy
- Quantum Signal Forecaster output
- Fusion AI output
- Reinforcement learning adaptiveness

Outputs:
- action_score (-1 -> +1)
- scaled_confidence
- persistent log/state
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path

from ai_core.cognitive_orchestrator import CognitiveOrchestrator
from ai_core.quantum_signal_forecaster import QuantumSignalForecaster
from ai_core.ai_fusion_core import AIFusionCore
from ai_core.rl_memory_loop import RLMemoryLoop

EXTERNAL_MEMORY = Path("/app/external_memory")
AI_STATE_DIR = EXTERNAL_MEMORY / "ai_state"
LOG_FILE = EXTERNAL_MEMORY / "logs" / "decision_kernel.log"

AI_STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class IntegrativeDecisionKernel:
    def __init__(self):
        self.orchestrator = CognitiveOrchestrator()
        self.forecaster = QuantumSignalForecaster()
        self.fusion = AIFusionCore()
        self.rl = RLMemoryLoop()
        self.last_decision = {}
        self.log("Integrative Decision Kernel initialized.")

    def log(self, msg):
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

    def strategy_to_numeric(self, strategy):
        mapping = {"AGGRESSIVE": 1.0, "NEUTRAL": 0.0, "DEFENSIVE": -0.5, "PAUSE": 0.0}
        return mapping.get(strategy, 0.0)

    def compute_action(self):
        # Gather all intelligence signals
        strategy = self.orchestrator.evaluate()
        strategy_num = self.strategy_to_numeric(strategy)

        quantum = self.forecaster.forecast()
        fusion_val = self.fusion.last_fusion_value
        adaptiveness = np.mean(self.rl.get_weights())

        # Integrative weighted sum
        weights = np.array([0.4, 0.3, 0.2, 0.1])  # Strategy | Quantum | Fusion | Adaptiveness
        signals = np.array([strategy_num, quantum["expected"], fusion_val, adaptiveness])
        action_score = float(np.tanh(np.dot(weights, signals)))

        # Confidence scaling inversely proportional to quantum uncertainty
        scaled_confidence = float(np.exp(-quantum["uncertainty"]) * abs(action_score))

        # Save decision state
        decision_state = {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": strategy,
            "action_score": action_score,
            "scaled_confidence": scaled_confidence,
            "fusion_output": fusion_val,
            "quantum_expected": quantum["expected"],
            "quantum_uncertainty": quantum["uncertainty"],
            "adaptiveness": adaptiveness
        }

        self.last_decision = decision_state
        self._save_state(decision_state)
        self.log(f"ActionScore={action_score:+.3f} | Conf={scaled_confidence:.3f} | Strategy={strategy}")
        return decision_state

    def _save_state(self, decision_state):
        with (AI_STATE_DIR / "decision_kernel_state.json").open("w", encoding="utf-8") as f:
            json.dump(decision_state, f, indent=2)

    def summary(self):
        return self.last_decision


if __name__ == "__main__":
    idk = IntegrativeDecisionKernel()
    for _ in range(10):
        decision = idk.compute_action()
        print(decision)
