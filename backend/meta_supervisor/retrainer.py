from ai_core.learning_engine import LearningEngine
from ai_core.memory_manager import MemoryManager
from pathlib import Path
import time, json

class Retrainer:
    def __init__(self, model_dir="/app/external_memory/models"):
        self.model_dir = Path(model_dir)
        self.engine = LearningEngine()
        self.memory = MemoryManager()

    def retrain_if_needed(self, drift_detected):
        if not drift_detected: return "no_drift"
        print("🧩 Drift detected — initiating retraining cycle...")
        new_model_path = self.model_dir / f"model_retrain_{int(time.time())}.bin"
        # Simulated retraining
        self.engine.reinforce("retrain_event", 1.0, "meta")
        self.memory.log_event("Retraining complete, model updated.")
        new_model_path.write_text("dummy_model_weights")
        return "model_updated"
