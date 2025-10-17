"""
AI Fusion Core
--------------
Central intelligence layer that unifies multiple AI subsystems:
- Market sentiment (NeuralMarketSentiment)
- Technical model predictions
- Reinforcement signals (simulated)
- Adaptive weight fusion

All results are cached in external memory for persistence.
"""

import json
from datetime import datetime
from pathlib import Path
import numpy as np

from ai_core.neural_market_sentiment import NeuralMarketSentiment

EXTERNAL_MEMORY = Path("/app/external_memory")
AI_STATE_DIR = EXTERNAL_MEMORY / "ai_state"
LOG_FILE = EXTERNAL_MEMORY / "logs" / "fusion_core.log"

AI_STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class AIFusionCore:
    def __init__(self):
        self.sentiment_engine = NeuralMarketSentiment()
        self.last_fusion_value = 0.0
        self.log("AI Fusion Core initialized.")

    def log(self, msg: str):
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

    def _mock_market_signal(self):
        """Simulated signal from a technical model (placeholder)."""
        return np.random.uniform(-1, 1)

    def _mock_rl_feedback(self):
        """Reinforcement signal (simulated)."""
        return np.random.uniform(-0.2, 0.2)

    def fuse_signals(self):
        """
        Combine multiple AI subsystems into a single decision signal.
        Fusion formula: weighted sum normalized through tanh.
        """
        sentiment = self.sentiment_engine.get_index()
        tech_signal = self._mock_market_signal()
        rl_signal = self._mock_rl_feedback()

        weights = np.array([0.5, 0.4, 0.1])
        signals = np.array([sentiment, tech_signal, rl_signal])
        fusion_raw = np.dot(weights, signals)
        fusion_output = float(np.tanh(fusion_raw))

        self.last_fusion_value = fusion_output
        self._save_state(sentiment, tech_signal, rl_signal, fusion_output)
        self.log(
            f"Fusion computed | Sentiment={sentiment:+.2f} | Tech={tech_signal:+.2f} | "
            f"RL={rl_signal:+.2f} | Output={fusion_output:+.2f}"
        )
        return fusion_output

    def _save_state(self, sentiment, tech, rl, fusion):
        state = {
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment": sentiment,
            "technical": tech,
            "reinforcement": rl,
            "fusion_output": fusion,
        }
        with (AI_STATE_DIR / "fusion_state.json").open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def summary(self):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "fusion_output": self.last_fusion_value,
        }


if __name__ == "__main__":
    fusion = AIFusionCore()
    for _ in range(10):
        fusion.sentiment_engine.update()
        fusion.fuse_signals()
    print(fusion.summary())
