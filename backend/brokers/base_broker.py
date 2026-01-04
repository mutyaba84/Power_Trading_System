# backend/app/brokers/base_broker.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseBroker(ABC):
    """
    Generic broker interface.
    All brokers (Alpaca, Binance, Simulation, etc.) must follow this contract.
    """

    def __init__(self, mode: str = "simulation") -> None:
        self.mode = mode

    @abstractmethod
    def connect(self) -> Any:
        """Establish connection with broker"""
        raise NotImplementedError

    @abstractmethod
    def place_order(self, symbol: str, qty: float, side: str, order_type: str = "market", **kwargs) -> Any:
        """
        Place an order.
        side: 'buy' or 'sell'
        order_type: 'market', 'limit'
        kwargs: broker-specific extras like limit_price, stop_price, time_in_force, etc.
        """
        raise NotImplementedError

    @abstractmethod
    def get_positions(self) -> Any:
        """Return current open positions"""
        raise NotImplementedError

    @abstractmethod
    def get_account(self) -> Any:
        """Return account info (cash, equity, buying power)"""
        raise NotImplementedError

    # ---------- OPTIONAL SAFETY EXTENSIONS ----------

    def is_live(self) -> bool:
        """Check if broker is in live trading mode"""
        return self.mode == "live"

    def supports_fractional(self) -> bool:
        """Override if broker supports fractional shares"""
        return False

    def supports_crypto(self) -> bool:
        """Override if broker supports crypto trading"""
        return False

    def health_check(self) -> Dict[str, Any]:
        """
        Optional: return basic health info without raising.
        """
        return {"ok": True, "mode": self.mode}
