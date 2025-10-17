import json, time, statistics
from pathlib import Path

class SentientRiskFirewall:
    """
    Real-time guardian that observes trading health metrics and enforces risk limits.
    """

    def __init__(self, external_memory="/app/external_memory", max_drawdown=0.15,
                 max_trade_loss=0.05, cooldown_period=60):
        self.root = Path(external_memory)
        self.firewall_dir = self.root / "firewall"
        self.firewall_dir.mkdir(parents=True, exist_ok=True)

        self.max_drawdown = max_drawdown
        self.max_trade_loss = max_trade_loss
        self.cooldown_period = cooldown_period

        self.last_equity = 100000
        self.high_watermark = self.last_equity
        self.active = True
        self.last_trigger_time = 0

    def _record_event(self, event):
        filename = self.firewall_dir / f"firewall_{int(time.time())}.json"
        filename.write_text(json.dumps(event, indent=2))

    def check_trade(self, trade_result):
        """
        Evaluates every trade for breach conditions.
        Returns dict with 'status' and optional 'action'.
        """
        equity = trade_result.get("equity", self.last_equity)
        pnl = trade_result.get("pnl", 0)
        timestamp = time.time()

        # update drawdown metrics
        if equity > self.high_watermark:
            self.high_watermark = equity
        drawdown = 1 - (equity / self.high_watermark)

        alert = {"timestamp": timestamp, "equity": equity,
                 "drawdown": round(drawdown,4), "pnl": pnl}

        if drawdown >= self.max_drawdown:
            alert["action"] = "HALT_TRADING"
            alert["reason"] = f"Drawdown {drawdown:.2%} exceeds {self.max_drawdown:.2%}"
            self.active = False
            self.last_trigger_time = timestamp
        elif pnl < -abs(self.last_equity * self.max_trade_loss):
            alert["action"] = "THROTTLE"
            alert["reason"] = f"Trade loss {pnl:.2f} exceeds limit"
            self.active = False
            self.last_trigger_time = timestamp
        else:
            alert["action"] = "OK"

        self._record_event(alert)
        self.last_equity = equity
        return alert

    def heartbeat(self):
        """Reactivate system after cooldown."""
        if not self.active and time.time() - self.last_trigger_time > self.cooldown_period:
            self.active = True
            self._record_event({
                "timestamp": time.time(),
                "action": "RESUME",
                "message": "Trading reactivated after cooldown"
            })
        return self.active
