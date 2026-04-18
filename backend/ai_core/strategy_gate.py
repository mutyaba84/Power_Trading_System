class StrategyGate:
    """
    🔥 INTELLIGENT STRATEGY GATE

    Now:
    - Uses regime as soft guidance
    - Uses performance to override
    - Blocks only truly bad strategies
    """

    def __init__(self, performance=None):
        self.performance = performance

        # 🔥 SOFT REGIME PREFERENCE (NOT HARD BLOCK)
        self.preference_map = {
            "CHOP": {"mean_reversion"},
            "TREND": {"momentum"},
            "UNKNOWN": {"mean_reversion"},
        }

    # -----------------------------------
    # MAIN CHECK
    # -----------------------------------
    def allowed(self, strategy: str, regime: str) -> bool:

        strategy = (strategy or "").lower()
        regime = (regime or "").upper()

        # -------------------------
        # 🔥 PERFORMANCE CHECK
        # -------------------------
        if self.performance:
            perf = self.performance.get_state(strategy, regime)

            # ❌ HARD BLOCK: cold + enough data
            if perf.get("state") == "cold" and perf.get("trades", 0) > 5:
                print(f"[GATE] Blocking cold strategy: {strategy}")
                return False

            # ✅ FORCE ALLOW: hot strategy
            if perf.get("state") == "hot":
                return True

        # -------------------------
        # 🔥 REGIME PREFERENCE (SOFT)
        # -------------------------
        preferred = self.preference_map.get(regime, set())

        if strategy in preferred:
            return True

        # -------------------------
        # 🔥 FALLBACK LOGIC
        # -------------------------
        # Allow non-preferred strategies with reduced confidence
        return True