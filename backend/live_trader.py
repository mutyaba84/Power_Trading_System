from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

from backend.utils.logger import get_logger

# Correct package imports
from backend.ai_core.learning_engine import LearningEngine
from backend.ai_core.memory_manager import MemoryManager

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
        self.broker = broker

        # Resolve mode
        self.mode = (mode or os.getenv("AI_MODE", "simulation")).lower()
        self.last_price: Optional[float] = None

        # Safety limits
        self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", "10000"))

        # Kill switch file location (default: <project>/external_memory/KILL_SWITCH)
        backend_dir = Path(__file__).resolve().parents[1]  # .../backend
        default_storage = backend_dir.parent / "external_memory"
        storage_base = Path(os.getenv("AI_STORAGE_PATH", str(default_storage)))
        storage_base.mkdir(parents=True, exist_ok=True)

        self.kill_switch_file = storage_base / "KILL_SWITCH"

        # Hard safety rule
        if self.mode == "live" and not self.broker:
            raise RuntimeError("LIVE mode requires a broker instance.")

        logger.info(f"LiveTrader initialized in {self.mode.upper()} mode.")
        logger.info(f"Kill switch path: {self.kill_switch_file}")

    # ---------------- SAFETY ----------------

    def is_killed(self) -> bool:
        """Check if KILL_SWITCH is activated."""
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

    # ---------------- RL / FEEDBACK ----------------

    def _reinforce_safe(self, key: str, reward: float, context: str = "momentum") -> None:
        """
        Call LearningEngine.reinforce in a way that won't break if its signature differs.
        Tries common patterns in order.
        """
        try:
            # Prefer positional (key, reward, context)
            self.engine.reinforce(key, reward, context)
            return
        except TypeError:
            pass
        except Exception as e:
            logger.warning(f"LearningEngine reinforce failed: {e}")
            return

        try:
            # Sometimes (reward, context)
            self.engine.reinforce(reward, context)
            return
        except TypeError:
            pass
        except Exception as e:
            logger.warning(f"LearningEngine reinforce failed: {e}")
            return

        try:
            # Sometimes just (reward)
            self.engine.reinforce(reward)
        except Exception as e:
            logger.warning(f"LearningEngine reinforce failed: {e}")

    # ---------------- DECISION ENGINE ----------------

    def decide(self, tick: Dict[str, Any]) -> str:
        """
        Core decision logic.
        Currently momentum-based placeholder.
        Later: replace with strategy engine output.
        """
        if self.is_killed():
            logger.warning("KILL_SWITCH active — holding position.")
            return "hold"

        price = tick.get("price")
        ts = tick.get("timestamp")

        if price is None:
            logger.warning("Tick missing price — holding.")
            return "hold"

        price_f = float(price)

        if self.last_price is None:
            self.last_price = price_f
            return "hold"

        diff = price_f - float(self.last_price)
        self.last_price = price_f

        if diff > 0.1:
            action = "buy"
        elif diff < -0.1:
            action = "sell"
        else:
            action = "hold"

        # Reinforcement feedback (placeholder reward)
        reward = random.uniform(-1, 1)
        key = f"{action}_{ts}" if ts is not None else f"{action}_{random.randint(1, 10_000_000)}"
        self._reinforce_safe(key=key, reward=reward, context="momentum")

        return action

    # ---------------- EXECUTION ----------------

    def execute_trade(self, tick: Dict[str, Any], trade_size: float = 1.0) -> Any:
        """
        Execute trade with full safety and mode awareness.
        Returns action string for simulation/paper, or broker order response for live.
        """
        if self.is_killed():
            try:
                self.memory.log_event("Trade blocked: KILL_SWITCH active.")
            except Exception:
                pass
            return "hold"

        action = self.decide(tick)

        if not self._validate_trade(action, trade_size):
            return "hold"

        trade_size = min(float(trade_size), float(self.max_order_size))

        # Log memory + console
        try:
            self.memory.log_event(
                f"Action={action} Price={tick.get('price')} Size={trade_size} Mode={self.mode}"
            )
        except Exception:
            pass

        # -------- SIMULATION / PAPER --------
        if self.mode in ("simulation", "paper"):
            logger.info(
                f"[{self.mode.upper()}] {action.upper()} | Size={trade_size} Price={tick.get('price')}"
            )
            return action

        # -------- LIVE EXECUTION --------
        if self.mode == "live":
            symbol = tick.get("symbol")
            if not symbol:
                logger.error("LIVE mode: tick missing symbol.")
                return "hold"

            if action == "hold":
                return "hold"

            logger.warning("LIVE TRADE EXECUTION")
            return self.broker.place_order(
                symbol=symbol,
                qty=trade_size,
                side=action,
                order_type="market",
            )

        return "hold"

    # ---------------- COMPATIBILITY ----------------

    def simulate_trade(self, tick: Dict[str, Any], trade_size: float = 1.0) -> Any:
        """Backward-compatible entry point used by main_controller."""
        return self.execute_trade(tick, trade_size)
