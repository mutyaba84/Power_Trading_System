from .base_broker import BaseBroker
import os
from alpaca_trade_api.rest import REST, TimeFrame
import logging

logger = logging.getLogger("AlpacaBroker")
logger.setLevel(logging.INFO)


class AlpacaBroker(BaseBroker):
    def __init__(self, mode=None):
        """
        mode: 'paper' or 'live'
        """
        self.mode = mode or os.getenv("AI_MODE", "simulation")
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")

        # Determine base URL
        if self.mode == "live":
            self.base_url = "https://api.alpaca.markets"
        else:
            # Paper or simulation mode
            self.base_url = "https://paper-api.alpaca.markets"

        self.client = None
        self.kill_switch_file = os.path.join(
            os.getenv("AI_STORAGE_PATH", "."), "KILL_SWITCH"
        )
        self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", 10000))

        logger.info(f"AlpacaBroker initialized in {self.mode.upper()} mode.")

    def is_killed(self):
        """Check if KILL_SWITCH is active."""
        return os.path.exists(self.kill_switch_file)

    def connect(self):
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API keys not set in environment!")

        self.client = REST(self.api_key, self.secret_key, self.base_url)
        account = self.client.get_account()
        logger.info(f"✅ Connected to Alpaca | Cash: {account.cash}")
        return account

    def place_order(self, symbol, qty, side, order_type="market"):
        if self.is_killed():
            logger.warning("KILL_SWITCH active — order aborted.")
            return None

        if qty > self.max_order_size:
            logger.warning(
                f"Order qty {qty} exceeds max limit {self.max_order_size}. Reducing."
            )
            qty = self.max_order_size

        order = self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force="gtc",
        )
        logger.info(f"Order submitted: {side} {qty} {symbol} [{order_type}]")
        return order

    def get_positions(self):
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")
        return self.client.list_positions()

    def get_account(self):
        if self.client is None:
            raise RuntimeError("Alpaca client not connected.")
        return self.client.get_account()
