from __future__ import annotations

from typing import Optional, List, Dict, Any
from backend.utils.logger import get_logger

logger = get_logger("AlpacaBroker")


class AlpacaBroker:
    """
    Alpaca execution adapter.
    Safe for reloads, multiprocessing, and simulation mode.
    """

    def __init__(self, mode: str = "simulation"):
        self.mode = mode
        self.connected = False

    # -------------------------------------------------
    # CONNECTION
    # -------------------------------------------------

    def connect(self):
        if self.connected:
            return

        logger.info(f"[ALPACA] Connecting (mode={self.mode})")

        # NOTE: real Alpaca auth would go here
        self.connected = True

    # -------------------------------------------------
    # MARKET DATA
    # -------------------------------------------------

    def fetch_bars(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch historical bars.
        """
        logger.info(f"[ALPACA DATA] Fetching bars for {symbol} (limit={limit})")

        # Placeholder stub (safe for simulation)
        return []

    # -------------------------------------------------
    # ORDER EXECUTION
    # -------------------------------------------------

    def place_order(
        self,
        *,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
    ):
        """
        Place an order (paper/live).
        """
        if not self.connected:
            self.connect()

        logger.info(
            f"[ALPACA ORDER] {side.upper()} {qty:.2f} {symbol} "
            f"type={order_type} mode={self.mode}"
        )

        # Stub for now — real Alpaca call later
        return {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "status": "filled" if self.mode != "live" else "submitted",
        }
