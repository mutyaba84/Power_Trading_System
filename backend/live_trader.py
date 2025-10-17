from ai_core.learning_engine import LearningEngine
from ai_core.memory_manager import MemoryManager
import random

class LiveTrader:
    def __init__(self, mode="simulation"):
        self.engine = LearningEngine()
        self.memory = MemoryManager()
        self.mode = mode
        self.last_price = None

    def decide(self, tick):
        """Simple evolving heuristic for demonstration."""
        price = tick["price"]
        if self.last_price is None:
            self.last_price = price
            return "hold"

        diff = price - self.last_price
        self.last_price = price

        if diff > 0.1:
            action = "buy"
        elif diff < -0.1:
            action = "sell"
        else:
            action = "hold"

        reward = random.uniform(-1, 1)
        self.engine.reinforce(f"{action}_{tick['timestamp']}", reward, context="momentum")
        return action

    def simulate_trade(self, tick):
        action = self.decide(tick)
        self.memory.log_event(f"Action: {action}, Price: {tick['price']}")
        return action
