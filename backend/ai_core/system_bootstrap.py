import threading
import time
from backend.ai_core.dummy_market_feed import run_dummy_feed


def start_ai_services():
    """
    Starts all AI background services.
    Runs exactly once at backend startup.
    """
    t = threading.Thread(
        target=run_dummy_feed,
        name="DummyMarketFeed",
        daemon=True
    )
    t.start()
    print("[SYSTEM] AI background services started")
