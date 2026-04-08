import threading
import time

from backend.main_controller import TradingController
from backend.utils.logger import get_logger

logger = get_logger("controller_runner")

_controller = None
_thread = None
_running = False


def run():
    global _controller, _running

    logger.info("[RUNNER] Starting trading controller")

    _controller = TradingController()
    _controller.start()

    _running = True

    while _running:
        time.sleep(1)


def start_controller():
    global _thread

    if _thread and _thread.is_alive():
        return

    _thread = threading.Thread(target=run, daemon=True)
    _thread.start()


def stop_controller():
    global _running

    _running = False
    logger.info("[RUNNER] Controller stopped")