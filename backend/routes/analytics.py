from fastapi import APIRouter
from backend.services.trade_analytics import TradeAnalytics
from backend.live_trader import trader

router = APIRouter()


@router.get("/analytics")
def get_analytics():

    analytics = TradeAnalytics(trader.trade_logger)

    return analytics.calculate()