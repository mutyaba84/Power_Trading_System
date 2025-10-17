from pathlib import Path
import json, pickle, time

class MemoryManager:
    def __init__(self, base_path: str = "/app/external_memory"):
        self.base = Path(base_path)
        self.paths = {
            "logs": self.base / "logs",
            "models": self.base / "models",
            "knowledge": self.base / "knowledge",
            "cache": self.base / "cache"
        }
        for p in self.paths.values():
            p.mkdir(parents=True, exist_ok=True)

    # ---------- Core Save/Load ----------
    def save_json(self, name: str, data: dict):
        file = self.paths["knowledge"] / f"{name}.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file

    def load_json(self, name: str):
        file = self.paths["knowledge"] / f"{name}.json"
        return json.load(open(file)) if file.exists() else {}

    def save_pickle(self, name: str, obj):
        file = self.paths["models"] / f"{name}.pkl"
        with open(file, "wb") as f:
            pickle.dump(obj, f)
        return file

    def load_pickle(self, name: str):
        file = self.paths["models"] / f"{name}.pkl"
        return pickle.load(open(file, "rb")) if file.exists() else None

    # ---------- Logging ----------
    def log_event(self, msg: str):
        file = self.paths["logs"] / f"session_{time.strftime('%Y%m%d')}.log"
        with open(file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
