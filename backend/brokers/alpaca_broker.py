from .base_broker import BaseBroker
import os
from alpaca_trade_api.rest import REST, TimeFrame

class AlpacaBroker(BaseBroker):
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = "https://paper-api.alpaca.markets"
        self.client = None

    def connect(self):
        self.client = REST(self.api_key, self.secret_key, self.base_url)
        account = self.client.get_account()
        print("✅ Connected to Alpaca | Equity:", account.cash)

    def place_order(self, symbol, qty, side, order_type="market"):
        order = self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force="gtc"
        )
        return order

    def get_positions(self):
        return self.client.list_positions()

    def get_account(self):
        return self.client.get_account()
