import time
from fastapi import APIRouter

from backend.services.trader_service import trader

router = APIRouter(prefix="/trader", tags=["trader"])


@router.get("/state")
def get_trader_state():
    """
    Exposes LiveTrader state for UI dashboard.
    """

    try:
        risk_state = trader.risk.get_state()
    except Exception:
        risk_state = {}

    return {
        "timestamp": time.time(),
        "regime": getattr(trader, "current_regime", "UNKNOWN"),
        "strategy": getattr(trader, "current_strategy", None),
        "position": getattr(trader, "position", "flat"),
        "equity": getattr(trader, "equity", 0),
        "risk": risk_state,
    }