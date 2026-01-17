from __future__ import annotations

import logging
import os
from typing import Any, Optional

from .base_broker import BaseBroker

logger = logging.getLogger("AlpacaBroker")
logger.setLevel(logging.INFO)


class AlpacaBroker(BaseBroker):
    """
    SAFE Alpaca broker adapter.

    MODES:
      - simulation (default)
      - paper       (ALLOWED)
      - live        (HARD BLOCKED)

    This file ONLY knows how to talk to Alpaca.
    It does NOT decide when trades happen.
    """

    def __init__(self, mode: Optional[str] = None) -> None:
        super().__init__(mode=mode or os.getenv("AI_MODE", "simulation"))

        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")

        # -------------------------------------------------
        # HARD SAFETY: LIVE TRADING IS BLOCKED
        # -------------------------------------------------
        if self.mode == "live":
            raise RuntimeError(
                "🚫 LIVE TRADING DISABLED. "
                "Remove this guard intentionally if you *really* want live trading."
            )

        # Paper & simulation both use paper endpoint
        self.base_url = "https://paper-api.alpaca.markets"

        self.client: Any = None

        storage = os.getenv("AI_STORAGE_PATH", ".")
        self.kill_switch_file = os.path.join(storage, "KILL_SWITCH")

        try:
            self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", "5"))
        except Exception:
            self.max_order_size = 5.0

        logger.info(
            f"🦙 AlpacaBroker initialized | MODE={self.mode.upper()} | MAX_QTY={self.max_order_size}"
        )

    # ------------------------------------------------------------------
    # SAFETY
    # ------------------------------------------------------------------

    def is_killed(self) -> bool:
        """Emergency kill switch via file."""
        return os.path.exists(self.kill_switch_file)

    # ------------------------------------------------------------------
    # CONNECTION
    # ------------------------------------------------------------------

    def connect(self) -> Any:
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca API keys not set in environment.")

        try:
            from alpaca_trade_api.rest import REST  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "alpaca_trade_api not installed. Run: pip install alpaca-trade-api"
            ) from e

        self.client = REST(
            key_id=self.api_key,
            secret_key=self.secret_key,
            base_url=self.base_url,
        )

        account = self.client.get_account()

        logger.info(
            f"✅ Connected to Alpaca PAPER | "
            f"Cash={getattr(account, 'cash', 'n/a')} | "
            f"Equity={getattr(account, 'equity', 'n/a')}"
        )

        return account

    # ------------------------------------------------------------------
    # ORDER EXECUTION
    # ------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        time_in_force: str = "gtc",
    ) -> Any:
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")

        if self.is_killed():
            logger.warning("🛑 KILL SWITCH ACTIVE — order blocked")
            return None

        if qty <= 0:
            raise ValueError("Order quantity must be positive.")

        if qty > self.max_order_size:
            raise ValueError(
                f"Order size {qty} exceeds MAX_ORDER_SIZE={self.max_order_size}"
            )

        if side not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")

        logger.info(
            f"📨 ALPACA ORDER | {side.upper()} {qty} {symbol} [{order_type}]"
        )

        return self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force,
        )

    # ------------------------------------------------------------------
    # ACCOUNT / DATA HELPERS
    # ------------------------------------------------------------------

    def get_positions(self) -> Any:
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")
        return self.client.list_positions()

    def get_account(self) -> Any:
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")
        return self.client.get_account()

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 200,
    ) -> Any:
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")

        try:
            from alpaca_trade_api.rest import TimeFrame  # type: ignore
        except Exception:
            TimeFrame = None

        tf = timeframe
        if TimeFrame is not None:
            mapping = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, TimeFrame.Unit.Minute),
                "15Min": TimeFrame(15, TimeFrame.Unit.Minute),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day,
            }
            tf = mapping.get(timeframe, TimeFrame.Minute)

        return self.client.get_bars(symbol, tf, limit=limit)
