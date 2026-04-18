class StrategyAllocator:
    """
    🔥 INTELLIGENT STRATEGY ALLOCATOR

    Now:
    - Uses regime as baseline
    - Overrides using performance (HOT / COLD)
    - Can disable losing strategies
    """

    def __init__(self, strategy_tracker=None, performance=None):
        self.strategy_tracker = strategy_tracker
        self.performance = performance

        # 🔥 AVAILABLE STRATEGIES
        self.strategies = ["momentum", "mean_reversion"]

    # -----------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------
    def select(self, regime: str, price: float | None = None) -> str:
        return self.choose(regime)

    # -----------------------------------
    # CORE LOGIC
    # -----------------------------------
    def choose(self, regime: str) -> str:
        regime = (regime or "").upper()

        # -------------------------
        # BASELINE (REGIME)
        # -------------------------
        if regime == "TREND":
            base = "momentum"
        elif regime == "CHOP":
            base = "mean_reversion"
        else:
            base = "mean_reversion"

        # -------------------------
        # 🔥 PERFORMANCE OVERRIDE
        # -------------------------
        if self.performance:
            best_strategy = base
            best_score = -999

            for strat in self.strategies:
                perf = self.performance.get_state(strat, regime)

                score = self._score_strategy(perf)

                # 🔥 HARD KILL BAD STRATEGIES
                if perf.get("state") == "cold" and perf.get("trades", 0) > 5:
                    print(f"[ALLOCATOR] Killing cold strategy: {strat}")
                    continue

                if score > best_score:
                    best_score = score
                    best_strategy = strat

            return best_strategy

        return base

    # -----------------------------------
    # 🔥 SCORING ENGINE
    # -----------------------------------
    def _score_strategy(self, perf: dict) -> float:
        """
        Convert performance → numeric score
        """

        if not perf:
            return 0

        state = perf.get("state", "neutral")
        win_rate = perf.get("win_rate", 0)
        avg_pnl = perf.get("avg_pnl", 0)
        trades = perf.get("trades", 0)

        score = 0

        # -------------------------
        # STATE WEIGHT
        # -------------------------
        if state == "hot":
            score += 2
        elif state == "cold":
            score -= 2

        # -------------------------
        # WIN RATE
        # -------------------------
        score += win_rate * 2

        # -------------------------
        # PNL CONTRIBUTION
        # -------------------------
        score += avg_pnl * 0.01

        # -------------------------
        # EXPERIENCE BONUS
        # -------------------------
        score += min(trades * 0.05, 1)

        return score