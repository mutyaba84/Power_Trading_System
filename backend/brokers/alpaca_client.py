from backend.brokers.config import get_alpaca_config
import yfinance as yf
import random


class AlpacaClient:
    def __init__(self):
        config = get_alpaca_config()
        self.symbol = config["symbol"]

        # 🔥 IMPORTANT: ensure API exists
        try:
            from alpaca_trade_api import REST
            self.api = REST(
                config["api_key"],
                config["secret_key"],
                base_url="https://paper-api.alpaca.markets" if config["paper"] else "https://api.alpaca.markets"
            )
        except Exception:
            self.api = None

        print(f"[DATA FEED] Using symbol: {self.symbol}")

    # ------------------------
    # PRICE (Yahoo fallback)
    # ------------------------
    def get_latest_price(self):
        print("🔥 USING YAHOO DATA")

        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period="1d", interval="1m")

            if data.empty:
                print("[YAHOO] No data returned")
                return None

            base_price = float(data["Close"].iloc[-1])
            noise = random.uniform(-0.02, 0.02)

            return round(base_price + noise, 4)

        except Exception as e:
            print(f"[YAHOO ERROR] {e}")
            return None

    def get_safe_price(self):
        try:
            return self.get_latest_price()
        except Exception as e:
            print(f"[YAHOO SAFE ERROR] {e}")
            return None

    # ------------------------
    # ACCOUNT
    # ------------------------
    def get_account_info(self):
        if not self.api:
            return {"cash": 0.0, "equity": 0.0, "buying_power": 0.0}

        account = self.api.get_account()
        return {
            "cash": float(account.cash),
            "equity": float(account.equity),
            "buying_power": float(account.buying_power),
        }

    # ------------------------
    # POSITION
    # ------------------------
    def get_position(self):
        if not self.api:
            return None

        try:
            pos = self.api.get_position(self.symbol)
            return {
                "side": "long" if float(pos.qty) > 0 else "short",
                "qty": abs(float(pos.qty)),
                "avg_entry_price": float(pos.avg_entry_price)
            }
        except Exception:
            return None