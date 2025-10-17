import json, time
from pathlib import Path
import numpy as np

class PerformanceTracker:
    def __init__(self, log_dir="/app/external_memory/reports"):
        self.log_dir = Path(log_dir); self.log_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.log_dir / f"performance_{int(time.time())}.json"
        self.records = []

    def log_trade(self, action, pnl, confidence):
        rec = {"t": time.time(), "a": action, "pnl": pnl, "conf": confidence}
        self.records.append(rec)

    def summarize(self):
        if not self.records: return {}
        pnl = [r["pnl"] for r in self.records]
        conf = [r["conf"] for r in self.records]
        stats = {
            "mean_pnl": float(np.mean(pnl)),
            "win_rate": float(np.mean([1 if p>0 else 0 for p in pnl])),
            "avg_confidence": float(np.mean(conf))
        }
        self.file.write_text(json.dumps({"summary": stats, "records": self.records[-100:]}))
        return stats
