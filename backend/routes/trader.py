from fastapi import APIRouter
from backend.services.trader_service import trader

router = APIRouter(prefix="/trader", tags=["trader"])


@router.get("/state")
def get_trader_state():
    """
    Exposes LiveTrader state for UI.
    """
    return {
        "regime": trader.current_regime,
        "strategy": trader.current_strategy,
        "position": getattr(trader, "position", "flat"),
        "equity": trader.equity,
        "risk": trader.risk.get_state(),
    }
