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

    def get_equity(self):
        try:
            account = self.client.get_account()
            return float(account.equity)
        except Exception as e:
            print(f"[BROKER ERROR] equity fetch failed: {e}")
            return None

    # -------------------------
    # POSITION
    # -------------------------
    def get_position(self, symbol):
        try:
            pos = self.client.get_open_position(symbol)
            return {
                "qty": float(pos.qty),
                "avg_price": float(pos.avg_entry_price)
            }
        except Exception:
            return None

    # -------------------------
    # ORDER HELPERS
    # -------------------------
    def calculate_qty(self, price, risk_pct):
        """
        Convert risk % → position size
        """
        equity = self.get_equity()
        if equity is None or price <= 0:
            return 0

        dollar_risk = equity * risk_pct
        qty = dollar_risk / price

        return max(0, round(qty, 4))

    # -------------------------
    # PLACE ORDER
    # -------------------------
    def place_order(self, symbol, qty, side):
        try:
            if qty <= 0:
                print("[BROKER] Skipping order: qty <= 0")
                return None

            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            print(f"[BROKER] Placing {side.upper()} {qty} {symbol}")

            return self.client.submit_order(order)

        except Exception as e:
            print(f"[BROKER ERROR] order failed: {e}")
            return None

    # -------------------------
    # CLOSE POSITION
    # -------------------------
    def close_position(self, symbol):
        try:
            print(f"[BROKER] Closing position: {symbol}")
            return self.client.close_position(symbol)
        except Exception as e:
            print(f"[BROKER ERROR] close failed: {e}")
            return None