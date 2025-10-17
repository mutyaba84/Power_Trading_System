import random, time
from ai_core.memory_manager import MemoryManager

class BrokerWatchdog:
    def __init__(self):
        self.memory = MemoryManager()
        self.brokers = ["Alpaca", "Binance", "Oanda"]

    def check_brokers(self):
        results = {}
        for b in self.brokers:
            status = random.choice(["OK", "FAIL"])
            self.memory.log_event(f"Broker {b} status: {status}")
            results[b] = status
        return results
