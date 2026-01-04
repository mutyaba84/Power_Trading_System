# File: backend/ai_core/sentient_risk_firewall.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class FirewallDecision:
    action: str = "ALLOW"   # ALLOW | HALT_TRADING | REDUCE_SIZE
    reason: str = "ok"
    severity: str = "low"   # low | medium | high


class SentientRiskFirewall:
    """
    Simple safety gate in front of execution results.
    """

    def __init__(self, max_abs_loss: float = 2000.0, max_volatility: float = 0.05, max_size: float = 200000.0):
        self.max_abs_loss = float(max_abs_loss)
        self.max_volatility = float(max_volatility)
        self.max_size = float(max_size)

    def check_trade(self, exec_result: Dict[str, Any]) -> Dict[str, Any]:
        pnl = float(exec_result.get("pnl", 0.0))
        vol = float(exec_result.get("volatility", 0.0))
        size = float(exec_result.get("size", 0.0))

        if size > self.max_size:
            d = FirewallDecision(action="REDUCE_SIZE", reason="size_too_large", severity="medium")
            return {"action": d.action, "reason": d.reason, "severity": d.severity}

        if vol > self.max_volatility:
            d = FirewallDecision(action="HALT_TRADING", reason="volatility_too_high", severity="high")
            return {"action": d.action, "reason": d.reason, "severity": d.severity}

        if pnl < -abs(self.max_abs_loss):
            d = FirewallDecision(action="HALT_TRADING", reason="loss_limit_breached", severity="high")
            return {"action": d.action, "reason": d.reason, "severity": d.severity}

        d = FirewallDecision()
        return {"action": d.action, "reason": d.reason, "severity": d.severity}
