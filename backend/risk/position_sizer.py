class PositionSizer:

    def __init__(
        self,
        base_size: float,
        min_size: float,
        max_size: float,
        target_volatility: float = 0.01,
    ):
        self.base_size = base_size
        self.min_size = min_size
        self.max_size = max_size
        self.target_volatility = target_volatility

    def size(self, confidence, volatility):

        if volatility is None:
            volatility = 0.01

        if confidence is None:
            confidence = 0.5

        vol_factor = self.target_volatility / max(volatility, 1e-6)

        raw_size = self.base_size * confidence * vol_factor

        final_size = max(self.min_size, min(raw_size, self.max_size))

        return float(final_size)