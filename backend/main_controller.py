from __future__ import annotations

import time
from typing import Any, Dict, Optional

from backend.utils.event_log import log_event
from backend.utils.logger import get_logger

from backend.live_trader import LiveTrader
from backend.data_feed import DataFeed
from backend.risk_manager import RiskManager

logger = get_logger("main_controller")


class TradingController:
    """
    Central orchestration loop:
      - fetch tick (SIM or ALPACA)
      - run trader decision
      - apply risk manager
      - log events
      - checkpoint meta systems
    """

    def __init__(self) -> None:
        # ---- Trader (owns broker + mode) ----
        self.trader = LiveTrader()

        # ---- Data Source Routing ----
        if self.trader.mode == "simulation":
            self.feed = DataFeed()
            logger.info("[CONTROLLER] Using simulated DataFeed")
        else:
            # AlpacaBroker implements next_tick()
            self.feed = self.trader._get_broker()
            logger.info("[CONTROLLER] Using AlpacaBroker for live data")

        # ---- Risk Manager (legacy wrapper) ----
        self.risk = RiskManager()

        # ---- Runtime State ----
        self.pnl_history = []
        self.current_episode = []
        self.tick_count = 0
        self.checkpoint_count = 0
        self.halt_reason: Optional[str] = None

        logger.info("[CONTROLLER] TradingController initialized")

    # -------------------------------------------------
    # MAIN STEP
    # -------------------------------------------------

    def step(self) -> Optional[Dict[str, Any]]:
        tick = self.feed.next_tick()

        if not tick:
            log_event("feed.empty")
            return None

        price = tick.get("price")
        if price is None:
            log_event("tick.invalid", reason="missing_price")
            return None

        if not self.risk.can_trade():
            self.halt_reason = "risk_halt"
            log_event("system.halt", reason=self.halt_reason)
            return {"event": "system.halt", "reason": self.halt_reason}

        # Placeholder confidence until ML model is wired
        confidence = 0.8

        sizing = self.risk.position_size(confidence=confidence)

        if not getattr(sizing, "allowed", False) or sizing.size <= 0:
            action = "hold"
            pnl = 0.0
        else:
            action = self.trader.simulate_trade(tick)
            pnl = 10.0 if action == "buy" else (-5.0 if action == "sell" else 0.0)

        self.risk.register_trade(
            action=action,
            pnl=pnl,
            size=float(getattr(sizing, "size", 0.0)),
            price=float(price),
        )

        self.pnl_history.append(pnl)
        self.current_episode.append(
            {"action": action, "pnl": pnl, "confidence": confidence}
        )

        payload = {
            "tick": self.tick_count,
            "action": action,
            "pnl": pnl,
            "confidence": confidence,
            "equity": float(getattr(self.trader, "equity", 0.0)),
            "price": float(price),
        }

        log_event("tick.processed", **payload)

        self.tick_count += 1
        return {"event": "tick.processed", **payload}

    # -------------------------------------------------
    # CHECKPOINT (EVERY N TICKS)
    # -------------------------------------------------

    def checkpoint(self) -> None:
        self.checkpoint_count += 1
        log_event("checkpoint.start", n=self.checkpoint_count)

        # Placeholder: future meta / retraining hooks go here

        self.current_episode = []
        log_event("checkpoint.done", n=self.checkpoint_count)

    # -------------------------------------------------
    # RUN LOOP
    # -------------------------------------------------

    def run(self, ticks: int = 200, sleep_s: float = 0.2) -> None:
        logger.info("[CONTROLLER] Run loop started")

        for i in range(ticks):
            ev = self.step()

            if ev and ev.get("event") == "system.halt":
                logger.warning(f"[CONTROLLER] Halted: {ev.get('reason')}")
                break

            if self.halt_reason:
                logger.warning(f"[CONTROLLER] Halted: {self.halt_reason}")
                break

            if (i + 1) % 20 == 0:
                self.checkpoint()

            time.sleep(sleep_s)

        log_event("system.stop", reason=self.halt_reason or "normal")
        logger.info("[CONTROLLER] Run loop finished")
