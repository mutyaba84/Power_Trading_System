from abc import ABC, abstractmethod
from typing import Optional, List


class Storage(ABC):
    # -------------------------
    # Trades
    # -------------------------
    @abstractmethod
    def log_trade(
        self,
        *,
        timestamp: float,
        symbol: str,
        side: str,
        size: float,
        price: float,
        strategy: str,
        confidence: float,
        pnl: Optional[float],
        simulated: bool,
    ) -> None:
        pass

    # -------------------------
    # Equity
    # -------------------------
    @abstractmethod
    def record_equity(self, timestamp: float, equity: float) -> None:
        pass

    @abstractmethod
    def get_equity_since(self, since_ts: float) -> List[float]:
        pass
