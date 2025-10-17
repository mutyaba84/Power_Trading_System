"""
Trading Engine – routes AI signals to mock execution.
"""
from utils.logger import get_logger
logger = get_logger("trading_engine")

class TradingEngine:
    def __init__(self):
        self.orders = []

    def execute_signal(self, signal):
        logger.info(f"Executing signal: {signal}")
        self.orders.append(signal)
        return {"executed": True, "signal": signal}

engine = TradingEngine()

