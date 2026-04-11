class StrategyEvolution:
    """
    Tracks strategy performance and allocates capital dynamically
    """

    def __init__(self):
        self.stats = {}

    # -------------------------
    def update(self, strategy: str, reward: float):
        if strategy not in self.stats:
            self.stats[strategy] = {
                "score": 0.0,
                "trades": 0
            }

        s = self.stats[strategy]

        s["trades"] += 1

        # exponential smoothing
        s["score"] = (s["score"] * 0.9) + (reward * 0.1)

    # -------------------------
    def get_weight(self, strategy: str) -> float:
        if strategy not in self.stats:
            return 1.0

        score = self.stats[strategy]["score"]

        # convert to positive weight
        weight = max(0.1, 1 + score)

        return weight

    # -------------------------
    def normalize(self):
        total = sum(self.get_weight(s) for s in self.stats)

        weights = {}
        for s in self.stats:
            weights[s] = self.get_weight(s) / total if total > 0 else 1.0

        return weights

    # -------------------------
    def should_trade(self, strategy: str) -> bool:
        if strategy not in self.stats:
            return True

        score = self.stats[strategy]["score"]

        # kill bad strategies
        return score > -0.3