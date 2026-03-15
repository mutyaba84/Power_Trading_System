from __future__ import annotations

import time
from typing import Any, Dict, Optional

from backend.utils.event_log import log_event
from backend.utils.logger import get_logger

from backend.live_trader import LiveTrader
from backend.data_feed import DataFeed
from backend.risk_manager import RiskManager
from backend.services.alpaca_live_feed import AlpacaLiveFeed

logger = get_logger("main_controller")


class TradingController:
    """
    Central orchestration loop:
      - fetch tick (SIM or ALPACA LIVE FEED)
      - run trader decision/execution
      - apply risk manager wrapper
      - log events
    """

    def __init__(self) -> None:
        self.trader = LiveTrader()

        if self.trader.mode == "simulation":
            self.feed = DataFeed()
            logger.info("[CONTROLLER] Using simulated DataFeed")
        else:
            self.feed = AlpacaLiveFeed()
            logger.info("[CONTROLLER] Using AlpacaLiveFeed for live data")

        self.risk = RiskManager()

        self.pnl_history = []
        self.current_episode = []
        self.tick_count = 0
        self.checkpoint_count = 0
        self.halt_reason: Optional[str] = None

        logger.info("[CONTROLLER] TradingController initialized")

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

        action = self.trader.execute_trade(tick)

        payload = {
            "tick": self.tick_count,
            "action": action,
            "equity": float(getattr(self.trader, "equity", 0.0)),
            "price": float(price),
            "regime": getattr(self.trader, "current_regime", "UNKNOWN"),
            "strategy": getattr(self.trader, "current_strategy", "none"),
        }

        log_event("tick.processed", **payload)

        self.tick_count += 1
        return {"event": "tick.processed", **payload}

    def checkpoint(self) -> None:
        self.checkpoint_count += 1
        log_event("checkpoint.start", n=self.checkpoint_count)
        self.current_episode = []
        log_event("checkpoint.done", n=self.checkpoint_count)

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
