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

    🔥 UPGRADED:
    - Adds HOT / COLD classification
    - Adds global performance state
    - Feeds RiskGovernor + MetaLearning
    """

    def __init__(self):
        self._data: Dict[str, Dict[str, PerformanceStats]] = defaultdict(
            lambda: defaultdict(PerformanceStats)
        )

        # 🔥 GLOBAL TRACKING
        self.total_trades = 0
        self.total_pnl = 0.0

    # -----------------------------------
    # RECORD TRADE
    # -----------------------------------
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

        # 🔥 GLOBAL UPDATE
        self.total_trades += 1
        self.total_pnl += pnl

    # -----------------------------------
    # 🔥 PERFORMANCE STATE (CRITICAL)
    # -----------------------------------
    def get_state(self, strategy: str, regime: str) -> dict:
        stats = self._data[strategy][regime]

        if stats.trades < 5:
            return {"state": "neutral"}

        win_rate = stats.win_rate
        avg_pnl = stats.avg_pnl

        # 🔥 CLASSIFICATION LOGIC
        if win_rate > 0.6 and avg_pnl > 0:
            state = "hot"
        elif win_rate < 0.4 or avg_pnl < 0:
            state = "cold"
        else:
            state = "neutral"

        return {
            "state": state,
            "win_rate": round(win_rate, 3),
            "avg_pnl": round(avg_pnl, 4),
            "trades": stats.trades,
        }

    # -----------------------------------
    # 🔥 GLOBAL STATE (SYSTEM HEALTH)
    # -----------------------------------
    def get_global_state(self) -> dict:
        if self.total_trades < 10:
            return {"state": "neutral"}

        avg_pnl = self.total_pnl / self.total_trades

        if avg_pnl > 0:
            state = "hot"
        elif avg_pnl < 0:
            state = "cold"
        else:
            state = "neutral"

        return {
            "state": state,
            "total_trades": self.total_trades,
            "total_pnl": round(self.total_pnl, 2),
            "avg_pnl": round(avg_pnl, 4),
        }

    # -----------------------------------
    # SNAPSHOT (UI SAFE)
    # -----------------------------------
    def snapshot(self) -> Dict[str, Dict[str, dict]]:
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