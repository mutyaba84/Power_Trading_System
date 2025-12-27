from ai_core.learning_engine import LearningEngine
from ai_core.memory_manager import MemoryManager
import random
import os
import logging


# ---------------- LOGGER ----------------
logger = logging.getLogger("LiveTrader")
logger.setLevel(logging.INFO)


class LiveTrader:
    def __init__(self, broker=None, mode=None):
        """
        broker: instance of BaseBroker (AlpacaBroker, SimulationBroker, etc.)
        mode: 'simulation', 'paper', or 'live'
        """

        self.engine = LearningEngine()
        self.memory = MemoryManager()
        self.broker = broker

        # Resolve mode
        self.mode = mode or os.getenv("AI_MODE", "simulation")
        self.last_price = None

        # Safety limits
        self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", 10000))
        self.kill_switch_file = os.path.join(
            os.getenv("AI_STORAGE_PATH", "."), "KILL_SWITCH"
        )

        # Hard safety rule
        if self.mode == "live" and not self.broker:
            raise RuntimeError("LIVE mode requires a broker instance.")

        logger.info(f"LiveTrader initialized in {self.mode.upper()} mode.")

    # ---------------- SAFETY ----------------

    def is_killed(self):
        """Check if KILL_SWITCH is activated."""
        return os.path.exists(self.kill_switch_file)

    def _validate_trade(self, action, trade_size):
        if action not in ("buy", "sell"):
            return False

        if trade_size <= 0:
            logger.warning("Invalid trade size.")
            return False

        if trade_size > self.max_order_size:
            logger.warning(
                f"Trade size {trade_size} exceeds max limit "
                f"{self.max_order_size}. Clamped."
            )
            return True

        return True

    # ---------------- DECISION ENGINE ----------------

    def decide(self, tick):
        """Core trading decision logic."""
        if self.is_killed():
            logger.warning("KILL_SWITCH active — holding position.")
            return "hold"

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

        # Reinforcement feedback
        reward = random.uniform(-1, 1)
        self.engine.reinforce(
            key=f"{action}_{tick['timestamp']}",
            reward=reward,
            context="momentum"
        )

        return action

    # ---------------- EXECUTION ----------------

    def execute_trade(self, tick, trade_size=1):
        """Execute trade with full safety and mode awareness."""

        if self.is_killed():
            self.memory.log_event("Trade blocked: KILL_SWITCH active.")
            return "hold"

        action = self.decide(tick)

        if not self._validate_trade(action, trade_size):
            return "hold"

        trade_size = min(trade_size, self.max_order_size)

        self.memory.log_event(
            f"Action={action} Price={tick['price']} Size={trade_size} Mode={self.mode}"
        )

        # -------- SIMULATION / PAPER --------
        if self.mode in ("simulation", "paper"):
            logger.info(
                f"[{self.mode.upper()}] {action.upper()} | "
                f"Size={trade_size} Price={tick['price']}"
            )
            return action

        # -------- LIVE EXECUTION --------
        if self.mode == "live":
            logger.warning("LIVE TRADE EXECUTION")
            order = self.broker.place_order(
                symbol=tick["symbol"],
                qty=trade_size,
                side=action,
                order_type="market"
            )
            return order

        return "hold"

    # ---------------- COMPATIBILITY ----------------

    def simulate_trade(self, tick, trade_size=1):
        """Backward-compatible entry point."""
        return self.execute_trade(tick, trade_size)
