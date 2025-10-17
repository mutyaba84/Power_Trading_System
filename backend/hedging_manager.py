import json
from pathlib import Path
import time

EXTERNAL_MEMORY = Path("D:/AI_Trading_Storage")
AI_STATE_DIR = EXTERNAL_MEMORY / "ai_state"
CORRELATION_FILE = AI_STATE_DIR / "correlations.json"

class HedgingManager:
    def __init__(self, broker, max_hedge=0.5):
        self.broker = broker
        self.max_hedge = max_hedge  # max hedge fraction per position
        self.correlations = self.load_correlations()

    def load_correlations(self):
        if CORRELATION_FILE.exists():
            with open(CORRELATION_FILE, "r") as f:
                return json.load(f)
        return {}

    def compute_hedge(self, symbol, qty):
        """Determine hedge positions based on correlations"""
        hedge_orders = []
        correlated_assets = self.correlations.get(symbol, {})
        for asset, corr in correlated_assets.items():
            if abs(corr) > 0.5:  # only hedge strong correlations
                hedge_qty = int(qty * corr * self.max_hedge)
                side = "sell" if qty > 0 else "buy"
                hedge_orders.append({"symbol": asset, "qty": abs(hedge_qty), "side": side})
        return hedge_orders

    def execute_hedges(self, symbol, qty):
        orders = self.compute_hedge(symbol, qty)
        for order in orders:
            self.broker.place_order(order["symbol"], order["qty"], order["side"])
        return orders
