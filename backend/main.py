from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.alpaca_live_feed import AlpacaLiveFeed
from backend.main_controller import TradingController
from backend.core.state import state
from backend.api.settings import router as settings_router




app = FastAPI(title="Power Trading System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_router, prefix="/api")

feed = AlpacaLiveFeed()
controller = TradingController()


@app.on_event("startup")
def startup():
    controller.start()
    feed.start()


@app.get("/")
def root():
    return {"status": "ONLINE"}


@app.get("/status")
def get_status():
    return state


@app.get("/metrics")
def get_metrics():
    return state


@app.get("/trades")
def get_trades():
    return state.get("trades", [])


@app.get("/logs")
def get_logs():
    return state.get("logs", [])[-50:]