from __future__ import annotations

import time
import math
from typing import Optional, Union

from backend.utils.logger import get_logger

logger = get_logger("RiskGovernor")


class RiskGovernor:
    """
    Advanced adaptive risk controller with:

    - Confidence scaling (non-linear)
    - Volatility dampening (exponential)
    - Regime awareness (TREND / CHOP)
    - Meta-learning awareness (hot / cold system)
    - Loss streak protection
    - Cooldown system
    - Capital efficiency boost (unused capital)
    - Safe risk clamping
    """

    def __init__(self):
        self.loss_streak: int = 0
        self.cooldown_until: Optional[float] = None

        # Base risk per strategy (fraction of equity)
        self.base_risk = {
            "momentum": 0.004,
            "mean_reversion": 0.0025,
        }

        self.max_loss_streak = 3
        self.cooldown_seconds = 2.5

        # Risk boundaries
        self.min_risk = 0.001   # 0.1%
        self.max_risk = 0.025   # 2.5%

    # -------------------------------------------------
    # RISK EVALUATION
    # -------------------------------------------------

    def evaluate(
        self,
        *,
        action: str,
        confidence: float,
        equity: float,
        volatility: float,
        strategy: str,
        regime: str = "NEUTRAL",
        performance: Union[str, dict] = "neutral",  # 🔥 supports dict or string
        deploy_pct: float = 0.25,
        ts: Optional[float] = None,
    ) -> float:
        """
        Returns fraction of equity allowed to risk.
        """

        now = ts or time.time()

        # -------------------------
        # COOLDOWN GUARD
        # -------------------------
        if self.cooldown_until and now < self.cooldown_until:
            logger.warning("[RISK] Cooldown active — trade blocked")
            return 0.0

        if action not in ("buy", "sell"):
            return 0.0

        base = self.base_risk.get(strategy, 0.002)

        # -------------------------
        # 1. CONFIDENCE FACTOR
        # -------------------------
        conf = max(0.0, min(confidence, 1.0))
        confidence_factor = 0.5 + (conf ** 1.5)

        # -------------------------
        # 2. VOLATILITY FACTOR
        # -------------------------
        vol = max(0.0, volatility)
        vol_factor = math.exp(-vol)

        # -------------------------
        # 3. REGIME FACTOR
        # -------------------------
        if regime == "TREND":
            regime_factor = 1.25
        elif regime == "CHOP":
            regime_factor = 0.6
        else:
            regime_factor = 1.0

        # -------------------------
        # 4. LOSS STREAK FACTOR
        # -------------------------
        drawdown_factor = max(0.4, 1 - (self.loss_streak * 0.2))

        # -------------------------
        # 5. META PERFORMANCE FACTOR
        # -------------------------
        perf_state = "neutral"

        if isinstance(performance, dict):
            # future-proof: if meta returns structured data
            perf_state = performance.get("state", "neutral")
        elif isinstance(performance, str):
            perf_state = performance

        if perf_state == "hot":
            perf_factor = 1.2
        elif perf_state == "cold":
            perf_factor = 0.6
        else:
            perf_factor = 1.0

        # -------------------------
        # 6. CAPITAL EFFICIENCY BOOST 🔥
        # -------------------------
        # lower deploy_pct → slightly higher aggression
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
            unused_capital_factor
        )

        # Clamp to safe bounds
        risk_pct = max(self.min_risk, min(self.max_risk, risk_pct))

        logger.info(
            f"[RISK] strat={strategy} conf={conf:.2f} vol={vol:.2f} "
            f"regime={regime} perf={perf_state} ls={self.loss_streak} "
            f"deploy={deploy_pct:.2f} risk={risk_pct:.4f}"
        )

        return risk_pct

    # -------------------------------------------------
    # POST-TRADE UPDATE
    # -------------------------------------------------

    def update_after_trade(self, *, pnl: float, equity: float):
        now = time.time()

        if pnl < 0:
            self.loss_streak += 1

            if self.loss_streak >= self.max_loss_streak:
                self.cooldown_until = now + self.cooldown_seconds
                logger.warning("[RISK] Loss streak — entering cooldown")

        else:
            if self.loss_streak > 0:
                self.loss_streak -= 1

        # cooldown expiry
        if self.cooldown_until and now >= self.cooldown_until:
            logger.info("[RISK] Cooldown complete — resetting loss streak")
            self.cooldown_until = None
            self.loss_streak = 0

    # -------------------------------------------------
    # STATE (UI / API SAFE)
    # -------------------------------------------------

    def get_state(self):
        now = time.time()
        cooldown_active = bool(self.cooldown_until and now < self.cooldown_until)

        return {
            "cooldown": cooldown_active,
            "loss_streak": self.loss_streak,
            "max_loss_streak": self.max_loss_streak,
        }