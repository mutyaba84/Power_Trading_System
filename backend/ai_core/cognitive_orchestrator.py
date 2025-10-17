"""
Cognitive Strategy Orchestrator
-------------------------------
The high-level meta-controller that decides system behavior based on:
- Sentiment Index (market mood)
- Fusion Output (combined AI signals)
- Reinforcement Policy (adaptive weights)
- Internal thresholds (risk and confidence)

Outputs a 'Strategy Signal' = {AGGRESSIVE, NEUTRAL, DEFENSIVE, PAUSE}
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path

from ai_core.ai_fusion_core import AIFusionCore
from ai_core.rl_memory_loop import RLMemoryLoop

EXTERNAL_MEMORY = Path("/app/external_memory")
AI_STATE_DIR = EXTERNAL_MEMORY / "ai_state"
LOG_FILE = EXTERNAL_MEMORY / "logs" / "orchestrator.log"

AI_STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class CognitiveOrchestrator:
    def __init__(self):
        self.fusion = AIFusionCore()
        self.rl = RLMemoryLoop()
        self.last_strategy = "NEUTRAL"
        self.log("Cognitive Orchestrator initialized.")

    def log(self, msg):
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

    def evaluate(self):
        """Main decision loop."""
        # Update subsystems
        self.fusion.sentiment_engine.update()
        fusion_output = self.fusion.fuse_signals()
        rl_weights = np.array(self.rl.get_weights())

        confidence = abs(fusion_output)
        sentiment_bias = np.sign(self.fusion.sentiment_engine.get_index())
        adaptiveness = np.mean(rl_weights)

        # Strategy rules
        if confidence > 0.75 and sentiment_bias > 0:
            strategy = "AGGRESSIVE"
        elif 0.4 < confidence <= 0.75:
            strategy = "NEUTRAL"
        elif confidence <= 0.4 and sentiment_bias < 0:
            strategy = "DEFENSIVE"
        else:
            strategy = "PAUSE"

        # Adjust for adaptiveness (learning stability)
        if adaptiveness < 0.25:
            strategy = "PAUSE"

        self.last_strategy = strategy
        self._save_state(strategy, fusion_output, confidence, adaptiveness)
        self.log(f"Strategy={strategy} | Fusion={fusion_output:+.3f} | "
                 f"Conf={confidence:.2f} | Adapt={adaptiveness:.2f}")
        return strategy

    def _save_state(self, strategy, fusion_output, confidence, adaptiveness):
        state = {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": strategy,
            "fusion_output": fusion_output,
            "confidence": confidence,
            "adaptiveness": adaptiveness
        }
        with (AI_STATE_DIR / "orchestrator_state.json").open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def summary(self):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": self.last_strategy
        }


if __name__ == "__main__":
    orch = CognitiveOrchestrator()
    for _ in range(15):
        orch.evaluate()
    print("Final Strategy:", orch.summary())
