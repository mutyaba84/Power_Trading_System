from __future__ import annotations

import threading
import time
from typing import Optional

from backend.main_controller import TradingController
from backend.utils.event_log import log_event

_thread: Optional[threading.Thread] = None
_stop_flag = False


def start_controller(tick_sleep_s: float = 0.2, checkpoint_every: int = 20) -> None:
    """
    Starts the trading controller loop in a background thread.
    Safe to call multiple times (it won't start twice).
    """
    global _thread, _stop_flag

    if _thread and _thread.is_alive():
        return

    _stop_flag = False

    def run() -> None:
        log_event("controller.thread.start", sleep_s=tick_sleep_s, checkpoint_every=checkpoint_every)
        ctl = TradingController()
        i = 0

        while not _stop_flag:
            ev = ctl.step()

            if ev and ev.get("event") == "system.halt":
                log_event("controller.halt", reason=ev.get("reason"))
                break

            if ctl.halt_reason:
                log_event("controller.halt", reason=ctl.halt_reason)
                break

            i += 1
            if checkpoint_every > 0 and (i % checkpoint_every == 0):
                try:
                    ctl.checkpoint()
                except Exception as e:
                    log_event("controller.checkpoint.error", error=str(e))

            time.sleep(tick_sleep_s)

        log_event("controller.thread.stop")

    _thread = threading.Thread(target=run, daemon=True, name="ControllerThread")
    _thread.start()


def stop_controller() -> None:
    global _stop_flag
    _stop_flag = True
    log_event("controller.stop_flag.set")
