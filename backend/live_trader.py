from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

from backend.utils.logger import get_logger
from backend.ai_core.learning_engine import LearningEngine
from backend.ai_core.memory_manager import MemoryManager
from backend.ai_core.regime_classifier import RegimeClassifier
from backend.ai_core.strategy_gate import StrategyGate
from backend.ai_core.strategy_performance import StrategyPerformance
from backend.brokers.alpaca_broker import AlpacaBroker
from backend.risk.risk_governor import RiskGovernor

logger = get_logger("LiveTrader")


class LiveTrader:
    """
    Execution-facing trader with:
    - Regime hysteresis
    - Signal hysteresis (confirmation + one-shot)
    - Strategy gating
    - Position enforcement
    - Single-source risk & PnL
    """

    def __init__(self, broker: Any = None, mode: Optional[str] = None):
        # ---- Core AI ----
        self.engine = LearningEngine()
        self.memory = MemoryManager()

        # ---- Regime & Strategy ----
        self.regime = RegimeClassifier()
        self.strategy_gate = StrategyGate()
        self.strategy_performance = StrategyPerformance()

        self.current_regime: str = "UNKNOWN"
        self.current_strategy: str = "none"
        self._last_regime: Optional[str] = None

        # ---- Mode ----
        self.mode = (mode or os.getenv("AI_MODE", "simulation")).lower()

        # ---- Market State ----
        self.last_price: Optional[float] = None
        self.price_window: list[float] = []

        # ---- Capital & Risk ----
        self.risk = RiskGovernor()
        self.equity = float(os.getenv("START_EQUITY", "10000"))
        self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", "10000"))

        # ---- Broker ----
        self.broker = broker
        self._broker_initialized = False

        # ---- Signal hysteresis ----
        self.last_action: Optional[str] = None
        self.signal_count: int = 0
        self.min_signal_confirmations = 3
        self._signal_fired: bool = False

        # ---- Position State ----
        self.position: str = "flat"   # flat | long | short

        # ---- Kill Switch ----
        backend_dir = Path(__file__).resolve().parents[1]
        storage_base = Path(os.getenv("AI_STORAGE_PATH", backend_dir / "external_memory"))
        storage_base.mkdir(parents=True, exist_ok=True)
        self.kill_switch_file = storage_base / "KILL_SWITCH"

        logger.info(f"LiveTrader started in {self.mode.upper()} mode")
        logger.info(f"Initial equity: {self.equity:.2f}")

    # -------------------------------------------------
    # SAFETY
    # -------------------------------------------------

    def is_killed(self) -> bool:
        return self.kill_switch_file.exists()

    # -------------------------------------------------
    # BROKER
    # -------------------------------------------------

    def _get_broker(self) -> AlpacaBroker:
        if self.broker and self._broker_initialized:
            return self.broker

        self.broker = AlpacaBroker(mode=self.mode)
        self.broker.connect()
        self._broker_initialized = True
        return self.broker

    # -------------------------------------------------
    # LEARNING (SAFE)
    # -------------------------------------------------

    def _reinforce_safe(self, key: str, reward: float, context: str):
        for args in [(key, reward, context), (reward, context), (reward,)]:
            try:
                self.engine.reinforce(*args)
                return
            except Exception:
                continue

    # -------------------------------------------------
    # DECISION
    # -------------------------------------------------

    def decide(self, tick: Dict[str, Any]) -> str:
        if self.is_killed():
            return "hold"

        price = tick.get("price")
        if price is None:
            return "hold"

        price = float(price)

        # ---- REGIME UPDATE ----
        regime = self.regime.update(price)

        # reset everything on regime change
        if regime != self._last_regime:
            self.signal_count = 0
            self.last_action = None
            self._signal_fired = False
            self._last_regime = regime

        self.current_regime = regime

        # ---- STRATEGY SELECTION ----
        if regime == "CHOP":
            strategy = "mean_reversion"
            raw_action = self._mean_reversion_decide(price)
        elif regime == "TREND":
            strategy = "momentum"
            raw_action = self._momentum_decide(price)
        else:
            self.current_strategy = "none"
            return "hold"

        self.current_strategy = strategy

        # ---- STRATEGY GATE ----
        if not self.strategy_gate.allowed(strategy=strategy, regime=regime):
            logger.info(f"[GATE] {strategy} blocked in {regime}")
            return "hold"

        # ---- APPLY SIGNAL HYSTERESIS ----
        action = self._apply_signal_hysteresis(raw_action)
        if action == "hold":
            return "hold"

        # ---- POSITION CHECK ----
        if not self._position_allows(action):
            logger.info(
                f"[POSITION] Blocked {action.upper()} (position={self.position})"
            )
            return "hold"

        # ---- LEARNING SIGNAL ----
        reward = random.uniform(-1, 1)
        self._reinforce_safe(
            key=f"{strategy}|{regime}",
            reward=reward,
            context=f"regime={regime}",
        )

        return action

    # -------------------------------------------------
    # STRATEGIES
    # -------------------------------------------------

    def _momentum_decide(self, price: float) -> str:
        if self.last_price is None:
            self.last_price = price
            return "hold"

        diff = price - self.last_price
        self.last_price = price

        if diff > 0.1:
            return "buy"
        elif diff < -0.1:
            return "sell"
        return "hold"

    def _mean_reversion_decide(self, price: float) -> str:
        self.price_window.append(price)
        if len(self.price_window) > 10:
            self.price_window.pop(0)

        if len(self.price_window) < 10:
            return "hold"

        mean_price = sum(self.price_window) / len(self.price_window)

        if price < mean_price * 0.995:
            return "buy"
        elif price > mean_price * 1.005:
            return "sell"
        return "hold"

    # -------------------------------------------------
    # POSITION LOGIC
    # -------------------------------------------------

    def _position_allows(self, action: str) -> bool:
        if self.position == "flat":
            return True
        if self.position == "long" and action == "buy":
            return False
        if self.position == "short" and action == "sell":
            return False
        return True

    # -------------------------------------------------
    # SIGNAL HYSTERESIS
    # -------------------------------------------------

    def _apply_signal_hysteresis(self, action: str) -> str:
        if action == "hold":
            self.signal_count = 0
            self.last_action = None
            self._signal_fired = False
            return "hold"

        if action != self.last_action:
            self.signal_count = 1
            self.last_action = action
            self._signal_fired = False
        else:
            self.signal_count += 1

        if self.signal_count < self.min_signal_confirmations:
            logger.info(
                f"[HYSTERESIS] {action.upper()} waiting "
                f"({self.signal_count}/{self.min_signal_confirmations})"
            )
            return "hold"

        if self._signal_fired:
            return "hold"

        self._signal_fired = True
        return action

    # -------------------------------------------------
    # EXECUTION
    # -------------------------------------------------

    def execute_trade(self, tick: Dict[str, Any]) -> str:
        action = self.decide(tick)
        if action == "hold":
            return "hold"

        confidence = float(tick.get("confidence", 0.5))
        volatility = float(tick.get("volatility", 0.0))
        ts = tick.get("timestamp")

        risk_pct = self.risk.evaluate(
            action=action,
            confidence=confidence,
            equity=self.equity,
            volatility=volatility,
            strategy=self.current_strategy,
            ts=ts,
        )

        if risk_pct <= 0.0:
            return "hold"

        size = min(self.equity * risk_pct, self.max_order_size)

        logger.info(
            f"[EXEC] {action.upper()} strat={self.current_strategy} "
            f"size={size:.2f} equity={self.equity:.2f} regime={self.current_regime}"
        )

        # ---- SIMULATION ----
        if self.mode == "simulation":
            pnl = random.uniform(-size * 0.01, size * 0.01)
            self.equity += pnl
            self.risk.update_after_trade(pnl=pnl, equity=self.equity)

            # ---- POSITION UPDATE ----
            if action == "buy":
                self.position = "long"
            elif action == "sell":
                self.position = "short"

            # reset signal latch
            self._signal_fired = False
            self.signal_count = 0
            self.last_action = None

            self.strategy_performance.record(
                strategy=self.current_strategy,
                pnl=pnl,
                regime=self.current_regime,
            )

            logger.info(
                f"[SIM] {action.upper()} PnL={pnl:.2f} Equity={self.equity:.2f}"
            )
            return action

        # ---- PAPER / LIVE ----
        broker = self._get_broker()
        broker.place_order(
            symbol=tick.get("symbol", "SPY"),
            qty=size,
            side=action,
            order_type="market",
        )

        return action

    # -------------------------------------------------
    # COMPATIBILITY
    # -------------------------------------------------

    def simulate_trade(self, tick: Dict[str, Any], trade_size: float = 1.0):
        return self.execute_trade(tick)
