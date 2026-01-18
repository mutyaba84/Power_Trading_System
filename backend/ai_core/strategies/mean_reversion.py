from __future__ import annotations
from collections import deque


class MeanReversionStrategy:
    """
    Simple mean-reversion strategy for CHOP regime.
    """

    def __init__(self, window: int = 10, threshold: float = 0.002):
        self.window = window
        self.threshold = threshold
        self.prices = deque(maxlen=window)

    def decide(self, price: float) -> str:
        self.prices.append(price)

        if len(self.prices) < self.window:
            return "hold"

        mean_price = sum(self.prices) / len(self.prices)
        deviation = (price - mean_price) / mean_price

        if deviation > self.threshold:
            return "sell"
        elif deviation < -self.threshold:
            return "buy"

        return "hold"
