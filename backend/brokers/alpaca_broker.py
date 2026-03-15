from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class AlpacaBroker:
    """
    Execution layer for Alpaca.
    Handles order submission and account info.
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )

    # -------------------------------------------------
    # ACCOUNT
    # -------------------------------------------------

    def get_account(self):
        return self.client.get_account()

    def get_equity(self) -> float:
        account = self.client.get_account()
        return float(account.equity)

    # -------------------------------------------------
    # ORDER EXECUTION
    # -------------------------------------------------

    def place_order(self, symbol: str, qty: float, side: str, order_type: str = "market"):
        """
        Places a market order.
        """

        qty = int(qty)

        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )

        return self.client.submit_order(order_data)