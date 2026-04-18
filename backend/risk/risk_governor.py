from __future__ import annotations

import time
import math
from typing import Optional, Union

from backend.utils.logger import get_logger

logger = get_logger("RiskGovernor")


class RiskGovernor:

    def __init__(self):
        self.loss_streak: int = 0
        self.cooldown_until: Optional[float] = None

        self.base_risk = {
            "momentum": 0.004,
            "mean_reversion": 0.0025,
        }

        self.max_loss_streak = 3
        self.cooldown_seconds = 5  # 🔥 slightly longer cooldown

        self.min_risk = 0.001
        self.max_risk = 0.025

    # -------------------------
    # MAIN ENTRY (STANDARDIZED)
    # -------------------------
    def get_risk(self, **kwargs) -> float:
        return self.evaluate(**kwargs)

    # -------------------------
    # CORE LOGIC
    # -------------------------
    def evaluate(
        self,
        *,
        action: str,
        confidence: float,
        equity: float,              # 🔥 MUST BE TOTAL EQUITY
        volatility: float,
        strategy: str,
        regime: str = "NEUTRAL",
        performance: Union[str, dict] = "neutral",
        deploy_pct: float = 0.25,
        ts: Optional[float] = None,
    ) -> float:

        now = ts or time.time()

        # -------------------------
        # HARD SAFETY
        # -------------------------
        if equity <= 0:
            return 0.0

        action = action.lower()
        if action not in ("buy", "sell"):
            return 0.0

        if self.cooldown_until and now < self.cooldown_until:
            logger.info("[RISK] cooldown active → no trading")
            return 0.0

        # 🔥 extreme volatility stop
        if volatility > 0.6:
            logger.warning("[RISK] volatility too high → blocked")
            return 0.0

        base = self.base_risk.get(strategy, 0.002)

        # -------------------------
        # FACTORS
        # -------------------------
        conf = max(0.0, min(confidence, 1.0))
        confidence_factor = 0.6 + (conf ** 1.3)

        vol = max(0.0, volatility)
        vol_factor = math.exp(-vol * 0.8)

        if regime == "TREND":
            regime_factor = 1.3
        elif regime == "CHOP":
            regime_factor = 0.55
        else:
            regime_factor = 1.0

        drawdown_factor = max(0.4, 1 - (self.loss_streak * 0.2))

        perf_state = "neutral"
        margin_pressure = 0.0

        if isinstance(performance, dict):
            perf_state = performance.get("state", "neutral")
            margin_pressure = performance.get("margin_pressure", 0.0)
        elif isinstance(performance, str):
            perf_state = performance

        if perf_state == "hot":
            perf_factor = 1.2
        elif perf_state == "cold":
            perf_factor = 0.6
        else:
            perf_factor = 1.0

        # 🔥 margin safety
        margin_factor = max(0.3, 1 - margin_pressure)

        # 🔥 deploy scaling
        deploy_pct = max(0.01, min(deploy_pct, 1.0))
        unused_capital_factor = 1 + (1 - deploy_pct) * 0.5
        unused_capital_factor = min(unused_capital_factor, 1.5)

        # -------------------------
        # FINAL RISK
        # -------------------------
        risk_pct = (
            base *
            confidence_factor *
            vol_factor *
            regime_factor *
            drawdown_factor *
            perf_factor *
            unused_capital_factor *
            margin_factor
        )

        risk_pct = max(self.min_risk, min(self.max_risk, risk_pct))

        logger.info(
            f"[RISK] strat={strategy} conf={conf:.2f} vol={vol:.2f} "
            f"regime={regime} perf={perf_state} margin={margin_pressure:.2f} "
            f"risk={risk_pct:.4f}"
        )

        return risk_pct

    # -------------------------
    # POST-TRADE LEARNING
    # -------------------------
    def update_after_trade(self, *, pnl: float, equity: float):
        now = time.time()

        if pnl < 0:
            self.loss_streak += 1
            logger.warning(f"[RISK] loss streak increased → {self.loss_streak}")

            if self.loss_streak >= self.max_loss_streak:
                self.cooldown_until = now + self.cooldown_seconds
                logger.warning("[RISK] cooldown triggered")

        else:
            if self.loss_streak > 0:
                self.loss_streak -= 1

        if self.cooldown_until and now >= self.cooldown_until:
            self.cooldown_until = None
            self.loss_streak = 0
            logger.info("[RISK] cooldown reset")

    # -------------------------
    # STATE INSPECTION
    # -------------------------
    def get_state(self):
        now = time.time()

        return {
            "cooldown": bool(self.cooldown_until and now < self.cooldown_until),
            "loss_streak": self.loss_streak,
            "max_loss_streak": self.max_loss_streak,
        }