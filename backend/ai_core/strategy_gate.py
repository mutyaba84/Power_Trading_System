class StrategyGate:

    def __init__(self):

        self.allowed_map = {
            "CHOP": {"mean_reversion"},
            "TREND": {"momentum"},
            "UNKNOWN": {"mean_reversion"},
        }

    def allowed(self, strategy: str, regime: str) -> bool:

        strategy = (strategy or "").lower()
        regime = (regime or "").upper()

        allowed = self.allowed_map.get(regime)

        if not allowed:
            return False

        return strategy in allowed