import numpy as np
from backend.live_trader import trader


class TradeAnalytics:

    def __init__(self, trade_logger):
        self.trade_logger = trade_logger

    def calculate(self):

        trades = self.trade_logger.get_trades()

        if not trades:
            return {}

        pnls = [t["pnl"] for t in trades]

        total_trades = len(pnls)

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        win_rate = len(wins) / total_trades if total_trades else 0

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0

        profit_factor = abs(sum(wins) / sum(losses)) if losses else 0

        equity_curve = [t["equity"] for t in trades]

        returns = np.diff(equity_curve)

        sharpe = 0
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns)

        max_drawdown = 0
        peak = equity_curve[0]

        for equity in equity_curve:
            if equity > peak:
                peak = equity

            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 3),
            "avg_win": round(avg_win, 3),
            "avg_loss": round(avg_loss, 3),
            "profit_factor": round(profit_factor, 3),
            "sharpe": round(sharpe, 3),
            "max_drawdown": round(max_drawdown, 3),
            "equity": equity_curve[-1],
        }