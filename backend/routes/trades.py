from fastapi import APIRouter
from backend.services.trader_service import trader

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("")
def get_trades():
    """
    Returns current trading state for the dashboard.
    """

    return {
        "equity": trader.equity,
        "position": trader.position,
        "strategy": trader.current_strategy,
        "regime": trader.current_regime,
    }