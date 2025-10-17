"""
Quantum Signal Forecaster
-------------------------
Quantum-inspired stochastic forecaster for short-term market direction.
Simulates multiple parallel universes (Monte-Carlo-style samples)
and aggregates them into a probabilistic directional index.
All runs are local and stored in external memory.
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path

EXTERNAL_MEMORY = Path("/app/external_memory")
AI_STATE = EXTERNAL_MEMORY / "ai_state"
LOG_FILE = EXTERNAL_MEMORY / "logs" / "quantum_forecast.log"

AI_STATE.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class QuantumSignalForecaster:
    def __init__(self, n_samples: int = 512, temperature: float = 0.6):
        self.n_samples = n_samples
        self.temperature = temperature
        self.last_forecast = {"expected": 0.0, "uncertainty": 0.0}
        self.log("QuantumSignalForecaster initialized.")

    def log(self, msg):
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

    def _quantum_sample(self):
        """
        Simulate one 'quantum sample' = a random scenario
        drawn from a nonlinear potential field.
        """
        # stochastic interference between two latent waves
        phase_shift = np.random.uniform(-np.pi, np.pi)
        amplitude = np.sin(phase_shift) + np.random.normal(0, self.temperature)
        return np.tanh(amplitude)

    def forecast(self):
        """Generate a multi-sample probability cone forecast."""
        samples = np.array([self._quantum_sample() for _ in range(self.n_samples)])
        expected = float(np.mean(samples))
        uncertainty = float(np.std(samples))

        self.last_forecast = {
            "timestamp": datetime.utcnow().isoformat(),
            "expected": expected,
            "uncertainty": uncertainty,
            "confidence": float(np.exp(-uncertainty)),  # lower uncertainty → higher confidence
        }

        self._save_state()
        self.log(f"Forecast ⟶ Exp={expected:+.3f} | σ={uncertainty:.3f} | Conf={self.last_forecast['confidence']:.3f}")
        return self.last_forecast

    def _save_state(self):
        with (AI_STATE / "quantum_forecast.json").open("w", encoding="utf-8") as f:
            json.dump(self.last_forecast, f, indent=2)

    def summary(self):
        return self.last_forecast


if __name__ == "__main__":
    qf = QuantumSignalForecaster()
    for _ in range(10):
        qf.forecast()
    print("Latest forecast:", qf.summary())
