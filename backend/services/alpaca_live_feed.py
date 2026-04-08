import threading
import time

from backend.brokers.alpaca_client import AlpacaClient
from backend.core.state import state


class AlpacaLiveFeed:
    def __init__(self):
        self.client = AlpacaClient()
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()
        print("[FEED] Started")

    def stop(self):
        self.running = False
        print("[FEED] Stopped")

    def _run(self):
        while self.running:
            try:
                # 🔥 SAFE DATA CALL
                price = self.client.get_safe_price()

                # ✅ CORRECT CHECK (handles 0.0 safely)
                if price is not None:
                    state["price"] = price
                    print(f"[FEED] Price: {price}")
                else:
                    print("[FEED] No price received")

            except Exception as e:
                print(f"[FEED ERROR] {e}")

            time.sleep(1)