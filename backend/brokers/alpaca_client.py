from backend.brokers.config import get_alpaca_config
import yfinance as yf
import random



class AlpacaClient:
    def __init__(self):
        config = get_alpaca_config()
        self.symbol = config["symbol"]
        print(f"[DATA FEED] Using symbol: {self.symbol}")

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