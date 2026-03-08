import time
from collections import deque


class TradeLogger:

    def __init__(self, max_trades: int = 100):
        self.trades = deque(maxlen=max_trades)

    def log_trade(
        self,
        strategy: str,
        side: str,
        size: float,
        price: float,
        pnl: float,
        equity: float,
    ):

        trade = {
            "time": time.time(),
            "strategy": strategy,
            "side": side,
            "size": round(size, 4),
            "price": round(price, 4),
            "pnl": round(pnl, 4),
            "equity": round(equity, 4),
        }

        self.trades.append(trade)

    def get_trades(self):

        return list(self.trades)