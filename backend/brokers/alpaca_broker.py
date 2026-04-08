from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class AlpacaBroker:

    def __init__(self, api_key, secret_key, paper=True):
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )

    # -------------------------
    # ACCOUNT
    # -------------------------
    def get_account(self):
        return self.client.get_account()

    # -------------------------
    # POSITION
    # -------------------------
    def get_position(self, symbol):
        try:
            pos = self.client.get_open_position(symbol)
            return {
                "qty": float(pos.qty)
            }
        except Exception:
            return None

    # -------------------------
    # PLACE ORDER
    # -------------------------
    def place_order(self, symbol, qty, side):
        try:
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            return self.client.submit_order(order)

        except Exception as e:
            print(f"[BROKER ERROR] {e}")
            return None