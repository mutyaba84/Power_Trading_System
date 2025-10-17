"""
Reinforcement Learning Memory Loop
----------------------------------
Adaptive self-training for AIFusionCore.
Evaluates historical decisions and updates fusion weights to improve performance.
All computation and storage are local (external_memory/ai_state/).
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path

EXTERNAL_MEMORY = Path("/app/external_memory")
AI_STATE = EXTERNAL_MEMORY / "ai_state"
LOG_FILE = EXTERNAL_MEMORY / "logs" / "rl_memory.log"

AI_STATE.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_POLICY = {
    "weights": [0.5, 0.4, 0.1],
    "learning_rate": 0.05,
    "episodes_trained": 0
}


class RLMemoryLoop:
    def __init__(self):
        self.policy_path = AI_STATE / "rl_policy.json"
        self.policy = self._load_policy()
        self.log("RLMemoryLoop initialized.")

    def log(self, msg: str):
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

    def _load_policy(self):
        if self.policy_path.exists():
            with self.policy_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_POLICY.copy()

    def _save_policy(self):
        with self.policy_path.open("w", encoding="utf-8") as f:
            json.dump(self.policy, f, indent=2)

    def _simulate_reward(self, fusion_output: float):
        """
        Generate a pseudo-reward signal.
        Positive reward if direction matches simulated market drift.
        """
        market_drift = np.random.uniform(-1, 1)
        reward = -abs(fusion_output - market_drift)
        return reward

    def train_once(self, fusion_output: float):
        """
        Update fusion weights via simulated reward feedback.
        """
        reward = self._simulate_reward(fusion_output)
        w = np.array(self.policy["weights"])
        lr = self.policy["learning_rate"]

        # Gradient ascent step (mock)
        gradient = np.sign(reward) * np.random.uniform(0.9, 1.1, size=w.shape)
        w = w + lr * gradient
        w = np.clip(w, 0, 1)
        w = w / np.sum(w)

        self.policy["weights"] = w.tolist()
        self.policy["episodes_trained"] += 1

        self._save_policy()
        self.log(
            f"Episode {self.policy['episodes_trained']} | "
            f"Reward={reward:+.4f} | New Weights={w.round(3).tolist()}"
        )
        return reward

    def get_weights(self):
        return self.policy["weights"]


if __name__ == "__main__":
    rl = RLMemoryLoop()
    for i in range(25):
        fusion_output = np.random.uniform(-1, 1)
        rl.train_once(fusion_output)
    print("Updated Weights:", rl.get_weights())
