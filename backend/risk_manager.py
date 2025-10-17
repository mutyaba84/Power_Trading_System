class RiskManager:
    def __init__(self, starting_equity=100000):
        self.equity = starting_equity
        self.max_drawdown = 0.2  # 20%
        self.position = 0

    def update_equity(self, pnl):
        self.equity += pnl
        return self.equity

    def can_trade(self):
        # simple capital preservation rule
        return self.equity > (1 - self.max_drawdown) * 100000
