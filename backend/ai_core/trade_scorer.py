class TradeScorer:

    def __init__(self):
        # 🔥 LOWER BASELINE (more trades)
        self.base_threshold = 0.58

        self.performance_bias = 0.0

        self.learning_rate_win = 0.002
        self.learning_rate_loss = 0.006

    # -------------------------------------------------
    # 🔥 DYNAMIC THRESHOLD (LESS RESTRICTIVE)
    # -------------------------------------------------
    def get_dynamic_threshold(self, regime: str) -> float:
        if regime == "CHOP":
            base = 0.60   # 🔥 was 0.65 → too strict
        else:
            base = 0.58

        threshold = base + self.performance_bias

        return max(0.50, min(0.70, threshold))

    # -------------------------
    # SCORE
    # -------------------------
    def score(
        self,
        *,
        confidence: float,
        momentum: float,
        volatility: float,
        regime: str,
        price: float,
    ) -> float:

        conf = max(0.0, min(confidence, 1.0))

        # 🔥 MOMENTUM (LESS AGGRESSIVE NORMALIZATION)
        if price != 0:
            mom_raw = momentum / price
        else:
            mom_raw = 0.0

        mom_raw *= 500   # 🔥 reduced from 1000

        mom = (mom_raw + 1) / 2
        mom = max(0.0, min(mom, 1.0))

        # -------------------------
        # VOLATILITY QUALITY (RELAXED)
        # -------------------------
        vol = max(0.0, volatility)

        if vol < 0.04:
            vol_score = 0.4
        elif vol < 0.12:
            vol_score = 1.0
        elif vol < 0.25:
            vol_score = 0.8
        else:
            vol_score = 0.5

        # -------------------------
        # REGIME
        # -------------------------
        if regime == "TREND":
            regime_score = 1.0
        elif regime == "CHOP":
            regime_score = 0.7   # 🔥 increased from 0.5
        else:
            regime_score = 0.8

        score = (
            0.45 * conf +
            0.25 * mom +
            0.2 * vol_score +
            0.1 * regime_score
        )

        return round(score, 4)

    # -------------------------
    # ALLOW TRADE (SMART FILTER)
    # -------------------------
    def allow_trade(
        self,
        score: float,
        regime: str,
        performance,
    ) -> bool:

        if regime == "CHOP":
            base = 0.60
        else:
            base = self.base_threshold

        perf_state = "neutral"
        margin_pressure = 0.0

        if isinstance(performance, dict):
            perf_state = performance.get("state", "neutral")
            margin_pressure = performance.get("margin_pressure", 0.0)
        elif isinstance(performance, str):
            perf_state = performance

        # -------------------------
        # META LEARNING
        # -------------------------
        if perf_state == "cold":
            meta_adjustment = 0.04
        elif perf_state == "hot":
            meta_adjustment = -0.03
        else:
            meta_adjustment = 0.0

        # -------------------------
        # MARGIN CONTROL
        # -------------------------
        margin_adjustment = margin_pressure * 0.04

        threshold = (
            base +
            self.performance_bias +
            meta_adjustment +
            margin_adjustment
        )

        threshold = max(0.50, min(0.70, threshold))

        print(
            f"[SCORER] score={score:.3f} thr={threshold:.3f} "
            f"perf={perf_state} margin={margin_pressure:.2f}"
        )

        return score >= threshold

    # -------------------------
    # PERFORMANCE LEARNING
    # -------------------------
    def update_performance(self, reward: float):

        if reward < 0:
            self.performance_bias += self.learning_rate_loss
        else:
            self.performance_bias -= self.learning_rate_win

        self.performance_bias = max(-0.05, min(0.05, self.performance_bias))

        print(
            f"[SCORER] reward={reward:.3f} "
            f"bias={self.performance_bias:.3f}"
        )