import random


class StrategyAllocator:

    def __init__(self, tracker):

        self.tracker = tracker
        self.exploration_rate = 0.1

    def choose(self, regime):

        strategies = {
            "TREND": ["momentum", "mean_reversion"],
            "CHOP": ["mean_reversion", "momentum"]
        }

        candidates = strategies.get(regime, ["momentum"])

        # exploration (try other strategy sometimes)
        if random.random() < self.exploration_rate:
            return random.choice(candidates)

        # exploitation (choose best)
        scores = {
            s: self.tracker.score(s)
            for s in candidates
        }

        return max(scores, key=scores.get)