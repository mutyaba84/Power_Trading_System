from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from backend.utils.event_log import log_event
from backend.utils.logger import get_logger
from backend.utils.paths import storage_root

logger = get_logger("RiskManager")


@dataclass
class TradeDecision:
    allowed: bool
    reason: str = "ok"
    size: float = 0.0


class RiskManager:
    """
    Simple risk manager (paper/sim).

    Env:
      - PAPER_EQUITY (default 10000)
      - RISK_LIMIT (default 0.02)
      - MAX_ORDER_SIZE (default 1.0)  # for simulation sizing sanity
      - MAX_DRAWDOWN (optional absolute; if not set uses PAPER_EQUITY*RISK_LIMIT)
    """

    def __init__(self):
        self.start_equity = float(os.getenv("PAPER_EQUITY", "10000.0"))
        self.equity = float(self.start_equity)

        self.risk_limit = float(os.getenv("RISK_LIMIT", "0.02"))

        # drawdown is absolute currency amount
        env_dd = os.getenv("MAX_DRAWDOWN")
        self.max_drawdown = float(env_dd) if env_dd else float(self.start_equity * self.risk_limit)

        self.max_order_size = float(os.getenv("MAX_ORDER_SIZE", "1.0"))

        # logs in storage root
        root = storage_root()
        self.log_dir = root / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.risk_log = self.log_dir / "risk.log"

        log_event(
            "risk.init",
            start_equity=self.start_equity,
            risk_limit=self.risk_limit,
            max_drawdown=self.max_drawdown,
            max_order_size=self.max_order_size,
            storage=str(root),
        )

    def current_drawdown(self) -> float:
        return float(self.start_equity - self.equity)

    def can_trade(self) -> bool:
        dd = self.current_drawdown()
        ok = dd <= self.max_drawdown
        if not ok:
            log_event(
                "risk.halt",
                equity=self.equity,
                start_equity=self.start_equity,
                drawdown=dd,
                max_drawdown=self.max_drawdown,
            )
        return ok

    def position_size(self, confidence: float = 0.8) -> TradeDecision:
        """
        Very simple sizing:
        - if risk halted => not allowed
        - else size scales with confidence, clamped by MAX_ORDER_SIZE
        """
        if not self.can_trade():
            return TradeDecision(False, reason="risk_halt", size=0.0)

        conf = float(confidence)
        if conf < 0.0:
            conf = 0.0
        if conf > 1.0:
            conf = 1.0

        size = max(0.0, min(self.max_order_size, self.max_order_size * conf))
        return TradeDecision(True, reason="ok", size=size)

    def update_equity(self, pnl: float) -> float:
        self.equity = float(self.equity) + float(pnl)

        # write small audit line
        try:
            with self.risk_log.open("a", encoding="utf-8") as f:
                f.write(f"{time.time():.3f} equity={self.equity:.2f} pnl={float(pnl):.2f}\n")
        except Exception as e:
            logger.warning(f"Failed writing risk log: {e}")

        return self.equity

    def register_trade(self, action: str, pnl: float, size: float, price: Optional[float] = None) -> None:
        """
        One place to log trade + equity changes in a consistent structure for the UI/log stream.
        """
        self.update_equity(pnl)

        log_event(
            "trade.registered",
            action=action,
            pnl=float(pnl),
            size=float(size),
            price=price,
            equity=float(self.equity),
            drawdown=float(self.current_drawdown()),
        )
