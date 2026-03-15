import os
from alpaca_trade_api.stream import Stream

from backend.utils.logger import get_logger

logger = get_logger("AlpacaStream")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL")

SYMBOL = os.getenv("ALPACA_SYMBOL", "SPY")


class AlpacaStreamService:

    def __init__(self, on_tick_callback):
        self.on_tick = on_tick_callback

        self.stream = Stream(
            API_KEY,
            SECRET_KEY,
            base_url=BASE_URL,
            data_feed="iex",  # free market data
        )

    async def trade_handler(self, trade):

        price = float(trade.price)

        logger.info(f"[ALPACA TICK] {SYMBOL} price={price}")

        if self.on_tick:
            self.on_tick(price)

    def start(self):

        logger.info("[ALPACA] Starting market data stream")

        self.stream.subscribe_trades(self.trade_handler, SYMBOL)

        self.stream.run()