from fastapi import APIRouter
from backend.live_trader import trader

router = APIRouter()


@router.get("/strategy/performance")
def strategy_performance():

    return trader.strategy_tracker.stats()