from __future__ import annotations

import time
import math
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger("RiskGovernor")


class RiskGovernor:
    """
    Strategy-aware risk controller with confidence curves.
    """

    def __init__(self):
        self.loss_streak = 0
        self.cooldown_until: Optional[float] = None

        # Base risk per strategy (fraction of equity)
        self.base_risk = {
            "momentum": 0.004,        # 0.4%
            "mean_reversion": 0.0025, # 0.25%
        }

        self.max_loss_streak = 3
        self.cooldown_seconds = 2.5

    # -------------------------------------------------

    def evaluate(
        self,
        *,
        action: str,
        confidence: float,
        equity: float,
        volatility: float,
        strategy: str,
        ts: Optional[float] = None,
    ) -> float:
        """
        Returns fraction of equity allowed to risk.
        """

        now = ts or time.time()

        if self.cooldown_until and now < self.cooldown_until:
            logger.warning("[RISK] Cooldown active — trade blocked")
            return 0.0

        if action not in ("buy", "sell"):
            return 0.0

        base = self.base_risk.get(strategy, 0.002)

        # ---- confidence curve ----
        conf = max(0.0, min(confidence, 1.0))
        confidence_factor = math.sqrt(conf)

        # ---- volatility dampener ----
        vol_factor = 1.0 / (1.0 + volatility)

        risk_pct = base * confidence_factor * vol_factor

        logger.info(
            f"[RISK] strat={strategy} conf={conf:.2f} "
            f"vol={volatility:.2f} risk_pct={risk_pct:.4f}"
        )

        return max(0.0, risk_pct)

    # -------------------------------------------------

    def update_after_trade(self, *, pnl: float, equity: float):
        if pnl < 0:
            self.loss_streak += 1
            if self.loss_streak >= self.max_loss_streak:
                self.cooldown_until = time.time() + self.cooldown_seconds
                logger.warning("[RISK] Loss streak — entering cooldown")
        else:
            if self.loss_streak > 0:
                self.loss_streak -= 1

        if self.cooldown_until and time.time() >= self.cooldown_until:
            logger.info("[RISK] Cooldown complete — resetting loss streak")
            self.cooldown_until = None
            self.loss_streak = 0
