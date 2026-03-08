from collections import defaultdict



class StrategyTracker:

    def __init__(self):
        self.performance = defaultdict(lambda: {
            "wins": 0,
            "losses": 0,
            "pnl": 0.0,
            "trades": 0
        })

    def record_trade(self, strategy: str, pnl: float):

        data = self.performance[strategy]

        data["trades"] += 1
        data["pnl"] += pnl

        if pnl > 0:
            data["wins"] += 1
        else:
            data["losses"] += 1

    def score(self, strategy):

        data = self.performance[strategy]

        trades = data["trades"]

        if trades == 0:
            return 0.5

        win_rate = data["wins"] / trades

        pnl_score = data["pnl"] / trades

        return 0.7 * win_rate + 0.3 * pnl_score

    def stats(self):
        return self.performance