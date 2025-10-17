import json
from pathlib import Path
import time

EXTERNAL_MEMORY = Path("D:/AI_Trading_Storage")
RISK_LOG = EXTERNAL_MEMORY / "logs" / "risk_events.json"
RISK_LOG.parent.mkdir(parents=True, exist_ok=True)

def log_risk_event(event):
    RISK_LOG.touch(exist_ok=True)
    try:
        with RISK_LOG.open("r") as f:
            history = json.load(f)
    except:
        history = []
    history.append(event)
    with RISK_LOG.open("w") as f:
        json.dump(history, f, indent=2)

class RiskManager:
    def __init__(self, max_exposure=0.2):
        self.max_exposure = max_exposure  # fraction of total equity
        self.protective_mode = False

    def check_stop_loss(self, trade, equity):
        """Dynamic stop-loss based on volatility and AI confidence"""
        threshold = 0.02 + (1 - trade['confidence']) * 0.05
        if abs(trade['action_score']) > threshold:
            self.protective_mode = True
            log_risk_event({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "event": "Stop-Loss Triggered",
                "trade": trade,
                "equity": equity
            })
            return True
        return False

    def position_sizing(self, equity, confidence):
        """Determine safe position size"""
        size = equity * confidence * self.max_exposure
        return size

    def check_volatility(self, volatility_index):
        """Trigger protective mode if volatility too high"""
        if volatility_index > 50:  # example VIX threshold
            self.protective_mode = True
            log_risk_event({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "event": "High Volatility Pause",
                "volatility_index": volatility_index
            })
            return True
        return False

    def reset_protection(self):
        self.protective_mode = False
