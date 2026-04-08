class StrategyAllocator:
    """
    Responsible for selecting strategy based on regime.
    Clean interface used by TradingController.
    """

    def __init__(self, strategy_tracker=None):
        self.strategy_tracker = strategy_tracker

    # -----------------------------
    # CORE METHOD (USED EVERYWHERE)
    # -----------------------------
    def select(self, regime: str, price: float | None = None) -> str:
        """
        Main entrypoint expected by controller
        """
        return self.choose(regime)

    # -----------------------------
    # INTERNAL LOGIC
    # -----------------------------
    def choose(self, regime: str) -> str:
        regime = (regime or "").upper()

        if regime == "CHOP":
            return "mean_reversion"

        if regime == "TREND":
            return "momentum"

        return "mean_reversion"