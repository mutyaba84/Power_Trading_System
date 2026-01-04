# backend/app/brokers/alpaca_broker.py
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from .base_broker import BaseBroker

logger = logging.getLogger("AlpacaBroker")
logger.setLevel(logging.INFO)


class AlpacaBroker(BaseBroker):
    def __init__(self, mode: Optional[str] = None) -> None:
        """
        mode: 'paper' or 'live' or 'simulation'
        - live  => https://api.alpaca.markets
        - paper/simulation => https://paper-api.alpaca.markets
        """
        super().__init__(mode=mode or os.getenv("AI_MODE", "simulation"))
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")

        if self.mode == "live":
            self.base_url = "https://api.alpaca.markets"
        else:
            self.base_url = "https://paper-api.alpaca.markets"

        self.client: Any = None

        storage = os.getenv("AI_STORAGE_PATH", ".")
        self.kill_switch_file = os.path.join(storage, "KILL_SWITCH")

        try:
            self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", "10000"))
        except Exception:
            self.max_order_size = 10000.0

        logger.info(f"AlpacaBroker initialized in {self.mode.upper()} mode.")

    def is_killed(self) -> bool:
        """Check if KILL_SWITCH is active."""
        return os.path.exists(self.kill_switch_file)

    def connect(self) -> Any:
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API keys not set in environment!")

        try:
            from alpaca_trade_api.rest import REST  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "alpaca_trade_api is not installed. Install it to use AlpacaBroker."
            ) from e

        self.client = REST(self.api_key, self.secret_key, self.base_url)
        account = self.client.get_account()
        logger.info(f"✅ Connected to Alpaca | Cash: {getattr(account, 'cash', 'n/a')}")
        return account

    def place_order(self, symbol: str, qty: float, side: str, order_type: str = "market", **kwargs) -> Any:
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")

        if self.is_killed():
            logger.warning("KILL_SWITCH active — order aborted.")
            return None

        try:
            qty_f = float(qty)
        except Exception:
            logger.warning(f"Invalid qty={qty}. Order aborted.")
            return None

        if qty_f <= 0:
            logger.warning(f"Non-positive qty={qty_f}. Order aborted.")
            return None

        if qty_f > self.max_order_size:
            logger.warning(f"Order qty {qty_f} exceeds max limit {self.max_order_size}. Reducing.")
            qty_f = self.max_order_size

        side = str(side).strip().lower()
        if side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")

        order_type = str(order_type).strip().lower()
        if order_type not in ("market", "limit", "stop", "stop_limit"):
            # Keep default behavior safe; Alpaca supports more types, but we won’t guess.
            order_type = "market"

        tif = kwargs.pop("time_in_force", "gtc")
        limit_price = kwargs.pop("limit_price", None)
        stop_price = kwargs.pop("stop_price", None)

        submit_kwargs = dict(
            symbol=symbol,
            qty=qty_f,
            side=side,
            type=order_type,
            time_in_force=tif,
        )
        if limit_price is not None:
            submit_kwargs["limit_price"] = limit_price
        if stop_price is not None:
            submit_kwargs["stop_price"] = stop_price

        order = self.client.submit_order(**submit_kwargs)
        logger.info(f"Order submitted: {side} {qty_f} {symbol} [{order_type}]")
        return order

    def get_positions(self) -> Any:
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")
        return self.client.list_positions()

    def get_account(self) -> Any:
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")
        return self.client.get_account()

    def get_bars(self, symbol: str, timeframe: str = "1Min", limit: int = 200) -> Any:
        """
        Optional helper. Kept minimal & safe.
        timeframe examples: "1Min", "5Min", "15Min", "1Hour", "1Day"
        """
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")
        try:
            from alpaca_trade_api.rest import TimeFrame  # type: ignore
        except Exception:
            TimeFrame = None

        # If TimeFrame exists, map common strings. Otherwise just pass string through.
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
