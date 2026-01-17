from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

from backend.utils.logger import get_logger
from backend.ai_core.learning_engine import LearningEngine
from backend.ai_core.memory_manager import MemoryManager
from backend.brokers.alpaca_broker import AlpacaBroker

logger = get_logger("LiveTrader")


class LiveTrader:
    """
    LiveTrader = execution-facing trader interface.

    Modes:
      - simulation (default)
      - paper
      - live (requires broker)

    Goals:
      - Never crash orchestrator due to bad tick fields.
      - Safety controls: max order size + kill switch.
      - Compatible with varying LearningEngine.reinforce signatures.
    """

    def __init__(self, broker: Any = None, mode: Optional[str] = None):
        self.engine = LearningEngine()
        self.memory = MemoryManager()

        # Resolve mode
        self.mode = (mode or os.getenv("AI_MODE", "simulation")).lower()
        self.last_price: Optional[float] = None

        # Broker (lazy-init)
        self.broker = broker
        self._broker_initialized = False

        # Safety limits
        self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", "10000"))

        # Kill switch file
        backend_dir = Path(__file__).resolve().parents[1]
        default_storage = backend_dir.parent / "external_memory"
        storage_base = Path(os.getenv("AI_STORAGE_PATH", str(default_storage)))
        storage_base.mkdir(parents=True, exist_ok=True)
        self.kill_switch_file = storage_base / "KILL_SWITCH"

        # Hard safety
        if self.mode == "live" and not self.broker:
            raise RuntimeError("LIVE mode requires a broker instance.")

        logger.info(f"LiveTrader initialized in {self.mode.upper()} mode.")
        logger.info(f"Kill switch path: {self.kill_switch_file}")

    # ---------------- SAFETY ----------------

    def is_killed(self) -> bool:
        return self.kill_switch_file.exists()

    def _validate_trade(self, action: str, trade_size: float) -> bool:
        if action not in ("buy", "sell", "hold"):
            return False

        if action == "hold":
            return True

        if trade_size <= 0:
            logger.warning("Invalid trade size.")
            return False

        if trade_size > self.max_order_size:
            logger.warning(
                f"Trade size {trade_size} exceeds max limit {self.max_order_size}. Clamping."
            )
            return True

        return True

    # ---------------- BROKER ----------------

    def _get_broker(self) -> AlpacaBroker:
        """
        Lazy broker initialization.
        Only used for PAPER or LIVE modes.
        """
        if self.broker and self._broker_initialized:
            return self.broker

        self.broker = AlpacaBroker(mode=self.mode)
        self.broker.connect()
        self._broker_initialized = True
        return self.broker

    # ---------------- RL ----------------

    def _reinforce_safe(self, key: str, reward: float, context: str = "momentum") -> None:
        try:
            self.engine.reinforce(key, reward, context)
            return
        except Exception:
            pass
        try:
            self.engine.reinforce(reward, context)
            return
        except Exception:
            pass
        try:
            self.engine.reinforce(reward)
        except Exception as e:
            logger.warning(f"LearningEngine reinforce failed: {e}")

    # ---------------- DECISION ----------------

    def decide(self, tick: Dict[str, Any]) -> str:
        if self.is_killed():
            logger.warning("KILL_SWITCH active — holding.")
            return "hold"

        price = tick.get("price")
        ts = tick.get("timestamp")

        if price is None:
            return "hold"

        price_f = float(price)

        if self.last_price is None:
            self.last_price = price_f
            return "hold"

        diff = price_f - self.last_price
        self.last_price = price_f

        if diff > 0.1:
            action = "buy"
        elif diff < -0.1:
            action = "sell"
        else:
            action = "hold"

        reward = random.uniform(-1, 1)
        key = f"{action}_{ts or random.randint(1, 10_000_000)}"
        self._reinforce_safe(key, reward, "momentum")

        return action

    # ---------------- EXECUTION ----------------

    def execute_trade(self, tick: Dict[str, Any], trade_size: float = 1.0) -> Any:
        if self.is_killed():
            self.memory.log_event("Trade blocked: KILL_SWITCH active.")
            return "hold"

        action = self.decide(tick)

        if not self._validate_trade(action, trade_size):
            return "hold"

        trade_size = min(float(trade_size), float(self.max_order_size))

        self.memory.log_event(
            f"Action={action} Price={tick.get('price')} Size={trade_size} Mode={self.mode}"
        )

        # -------- SIMULATION --------
        if self.mode == "simulation":
            logger.info(
                f"[SIMULATION] {action.upper()} | Size={trade_size} Price={tick.get('price')}"
            )
            return action

        # -------- PAPER (ALPAC
