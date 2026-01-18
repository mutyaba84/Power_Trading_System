from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict


@dataclass
class PerformanceStats:
    trades: int = 0
    wins: int = 0
    pnl: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.wins / self.trades

    @property
    def avg_pnl(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.pnl / self.trades


class StrategyPerformance:
    """
    Tracks performance by (strategy, regime)
    Used for attribution, learning isolation, and future auto-weighting.
    """

    def __init__(self):
        self._data: Dict[str, Dict[str, PerformanceStats]] = defaultdict(
            lambda: defaultdict(PerformanceStats)
        )

    def record(
        self,
        *,
        strategy: str,
        regime: str,
        pnl: float,
    ) -> None:
        stats = self._data[strategy][regime]
        stats.trades += 1
        stats.pnl += pnl
        if pnl > 0:
            stats.wins += 1

    def snapshot(self) -> Dict[str, Dict[str, dict]]:
        """
        Safe read-only snapshot for UI / API
        """
        out: Dict[str, Dict[str, dict]] = {}
        for strat, regimes in self._data.items():
            out[strat] = {}
            for reg, stats in regimes.items():
                out[strat][reg] = {
                    "trades": stats.trades,
                    "win_rate": round(stats.win_rate, 3),
                    "pnl": round(stats.pnl, 2),
                    "avg_pnl": round(stats.avg_pnl, 4),
                }
        return out
