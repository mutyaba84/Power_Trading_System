import numpy as np

class RewardPolicy:
    def __init__(self, pnl_weight=0.7, risk_weight=0.3):
        self.pnl_weight = pnl_weight
        self.risk_weight = risk_weight

    def calculate(self, pnl_series, drawdown_series):
        avg_pnl = np.mean(pnl_series)
        avg_drawdown = np.mean(drawdown_series)
        reward = (self.pnl_weight * avg_pnl) - (self.risk_weight * avg_drawdown)
        return float(reward)
