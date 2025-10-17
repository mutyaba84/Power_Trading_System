import numpy as np, json, time
from pathlib import Path

class DriftDetector:
    def __init__(self, memory_path="/app/external_memory/models"):
        self.memory_path = Path(memory_path)
        self.drift_file = self.memory_path / "drift_status.json"

    def check_drift(self, recent_pnls):
        if len(recent_pnls) < 20: return False
        window_old, window_new = np.mean(recent_pnls[:10]), np.mean(recent_pnls[-10:])
        drift = window_new < 0.8 * window_old
        self.drift_file.write_text(json.dumps({"time": time.time(), "drift": drift}))
        return drift
