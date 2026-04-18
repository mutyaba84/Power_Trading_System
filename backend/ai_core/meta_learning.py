class MetaLearning:
    """
    🔥 SYSTEM-LEVEL INTELLIGENCE CONTROLLER

    Controls:
    - Aggression (risk scaling)
    - System confidence (hot / cold)
    - Stability detection
    """

    def __init__(self):
        self.recent_pnls = []
        self.window = 20

        self.performance = "neutral"
        self.streak = 0

    # -----------------------------------
    # 🔥 UPDATE FROM REAL TRADE PNL
    # -----------------------------------
    def update(self, pnl: float):
        self.recent_pnls.append(pnl)

        if len(self.recent_pnls) > self.window:
            self.recent_pnls.pop(0)

        avg = sum(self.recent_pnls) / len(self.recent_pnls)

        # -------------------------
        # 🔥 PERFORMANCE STATE
        # -------------------------
        if avg > 0:
            new_state = "hot"
        elif avg < 0:
            new_state = "cold"
        else:
            new_state = "neutral"

        # -------------------------
        # 🔥 STREAK TRACKING
        # -------------------------
        if pnl > 0:
            if self.streak >= 0:
                self.streak += 1
            else:
                self.streak = 1
        else:
            if self.streak <= 0:
                self.streak -= 1
            else:
                self.streak = -1

        self.performance = new_state

    # -----------------------------------
    # 🔥 SYSTEM STATE OUTPUT
    # -----------------------------------
    def get_state(self):
        return {
            "state": self.performance,
            "streak": self.streak,
            "confidence_boost": self._confidence_boost(),
        }

    # -----------------------------------
    # 🔥 CONFIDENCE MODIFIER
    # -----------------------------------
    def _confidence_boost(self) -> float:
        """
        Returns multiplier for risk engine
        """

        if self.performance == "hot":
            return 1.2 + min(self.streak * 0.05, 0.5)

        if self.performance == "cold":
            return max(0.5, 1 + self.streak * 0.05)

        return 1.0