class TradeScorer:
    """
    Scores trade quality from 0 → 1

    Features:
    - Confidence + momentum + volatility + regime scoring
    - Adaptive threshold via performance bias
    - Meta-learning integration (hot / cold system state)
    - Learns from REWARD (not just pnl)
    """

    def __init__(self):
        self.base_threshold = 0.62

        # 🔥 adaptive bias (learns over time)
        self.performance_bias = 0.0

        # 🔥 smoothing (prevents overreaction)
        self.learning_rate_win = 0.003
        self.learning_rate_loss = 0.008

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

        # -------------------------
        # 1. CONFIDENCE
        # -------------------------
        conf = max(0.0, min(confidence, 1.0))

        # -------------------------
        # 2. MOMENTUM (normalized)
        # -------------------------
        if price != 0:
            mom_raw = momentum / price
        else:
            mom_raw = 0.0

        # amplify small moves
        mom_raw *= 1000

        mom = (mom_raw + 1) / 2
        mom = max(0.0, min(mom, 1.0))

        # -------------------------
        # 3. VOLATILITY QUALITY
        # -------------------------
        vol = max(0.0, volatility)

        if vol < 0.05:
            vol_score = 0.2
        elif vol < 0.15:
            vol_score = 1.0
        elif vol < 0.30:
            vol_score = 0.7
        else:
            vol_score = 0.4

        # -------------------------
        # 4. REGIME ALIGNMENT
        # -------------------------
        if regime == "TREND":
            regime_score = 1.0
        elif regime == "CHOP":
            regime_score = 0.5
        else:
            regime_score = 0.7

        # -------------------------
        # FINAL SCORE
        # -------------------------
        score = (
            0.4 * conf +
            0.3 * mom +
            0.2 * vol_score +
            0.1 * regime_score
        )

        return round(score, 4)

    # -------------------------
    # ADAPTIVE DECISION
    # -------------------------
    def allow_trade(
        self,
        score: float,
        regime: str,
        performance: str,  # 🔥 meta-learning input
    ) -> bool:

        # -------------------------
        # BASE THRESHOLD
        # -------------------------
        if regime == "CHOP":
            base = 0.63
        else:
            base = self.base_threshold

        # -------------------------
        # META LEARNING ADJUSTMENT
        # -------------------------
        if performance == "cold":
            meta_adjustment = 0.03   # stricter
        elif performance == "hot":
            meta_adjustment = -0.02  # more aggressive
        else:
            meta_adjustment = 0.0

        # -------------------------
        # FINAL THRESHOLD
        # -------------------------
        threshold = base + self.performance_bias + meta_adjustment

        # clamp safety
        threshold = max(0.55, min(0.75, threshold))

        return score >= threshold

    # -------------------------
    # 🔥 PERFORMANCE FEEDBACK (REWARD-BASED)
    # -------------------------
    def update_performance(self, reward: float):
        """
        Adaptive learning from reward (NOT raw pnl)
        """

        if reward < 0:
            # losing → tighten system
            self.performance_bias += self.learning_rate_loss
        else:
            # winning → loosen slightly
            self.performance_bias -= self.learning_rate_win

        # clamp to safe range
        self.performance_bias = max(-0.05, min(0.05, self.performance_bias))

        # -------------------------
        # DEBUG (VERY USEFUL)
        # -------------------------
        print(
            f"[SCORER] reward={reward:.3f} "
            f"bias={self.performance_bias:.3f}"
        )