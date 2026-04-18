from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus


class AlpacaBroker:

    def __init__(self, api_key, secret_key, paper=True):
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )

    # -----------------------------------
    # ACCOUNT
    # -----------------------------------
    def get_account(self):
        try:
            return self.client.get_account()
        except Exception as e:
            print(f"[BROKER ERROR] get_account failed: {e}")
            return None

    def get_equity(self):
        try:
            account = self.client.get_account()
            return float(account.equity)
        except Exception as e:
            print(f"[BROKER ERROR] get_equity failed: {e}")
            return None

    # -----------------------------------
    # POSITION
    # -----------------------------------
    def get_position(self, symbol):
        try:
            pos = self.client.get_open_position(symbol)
            return {
                "qty": float(pos.qty),
                "qty_available": float(pos.qty_available),
                "avg_price": float(pos.avg_entry_price),
            }
        except Exception:
            return None

    def close_position(self, symbol):
        try:
            print(f"[BROKER] Closing position: {symbol}")
            return self.client.close_position(symbol)
        except Exception as e:
            print(f"[BROKER ERROR] close_position failed: {e}")
            return None

    # -----------------------------------
    # ORDER HELPERS
    # -----------------------------------
    def calculate_qty(self, price, risk_pct):
        equity = self.get_equity()

        if equity is None or price <= 0 or risk_pct <= 0:
            return 0

        dollar_risk = equity * risk_pct
        qty = dollar_risk / price

        return max(0, int(qty))

    # -----------------------------------
    # PLACE ORDER
    # -----------------------------------
    def place_order(self, symbol, qty, side):
        try:
            qty = int(qty)

            if qty <= 0:
                print("[BROKER] Skipping order: qty <= 0")
                return False

            side = side.lower()
            if side not in {"buy", "sell"}:
                print(f"[BROKER ERROR] invalid side: {side}")
                return False

            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            print(f"[BROKER] Placing {side.upper()} {qty} {symbol}")
            self.client.submit_order(order)
            return True

        except Exception as e:
            print(f"[BROKER ERROR] order failed: {e}")
            return False

    # -----------------------------------
    # ORDER VISIBILITY
    # -----------------------------------
    def list_orders(self):
        try:
            request = GetOrdersRequest(status=QueryOrderStatus.OPEN)
            orders = self.client.get_orders(filter=request)

            return [
                {
                    "id": str(o.id),
                    "status": str(o.status).lower(),
                    "symbol": str(o.symbol),
                    "qty": float(o.qty),
                    "filled_qty": float(getattr(o, "filled_qty", 0) or 0),
                }
                for o in orders
            ]

        except TypeError:
            # fallback for SDK variants that use positional request
            try:
                request = GetOrdersRequest(status=QueryOrderStatus.OPEN)
                orders = self.client.get_orders(request)

                return [
                    {
                        "id": str(o.id),
                        "status": str(o.status).lower(),
                        "symbol": str(o.symbol),
                        "qty": float(o.qty),
                        "filled_qty": float(getattr(o, "filled_qty", 0) or 0),
                    }
                    for o in orders
                ]
            except Exception as e:
                print(f"[BROKER ERROR] list_orders failed: {e}")
                return []

        except Exception as e:
            print(f"[BROKER ERROR] list_orders failed: {e}")
            return []

    def get_order(self, order_id):
        try:
            o = self.client.get_order_by_id(order_id)
            return {
                "id": str(o.id),
                "status": str(o.status).lower(),
                "symbol": str(o.symbol),
                "qty": float(o.qty),
                "filled_qty": float(getattr(o, "filled_qty", 0) or 0),
            }
        except Exception as e:
            print(f"[BROKER ERROR] get_order failed: {e}")
            return None

    # -----------------------------------
    # ORDER CANCELLATION
    # -----------------------------------
    def cancel_order(self, order_id):
        try:
            self.client.cancel_order_by_id(order_id)
            print(f"[BROKER] Cancelled order {order_id}")
            return True
        except Exception as e:
            print(f"[BROKER ERROR] cancel_order failed: {e}")
            return False

    def cancel_all_orders(self):
        try:
            orders = self.list_orders()

            if not orders:
                print("[BROKER] No open orders to cancel")
                return True

            for order in orders:
                self.cancel_order(order["id"])

            print(f"[BROKER] Cancelled {len(orders)} open orders")
            return True

        except Exception as e:
            print(f"[BROKER ERROR] cancel_all_orders failed: {e}")
            return False