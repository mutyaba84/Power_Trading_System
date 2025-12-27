"""
Power Trading System – backend entry point
Runs the FastAPI server and routes core operations.
"""
from fastapi import FastAPI
from backend.utils.logger import get_logger
from backend.api_server import router   # ✅ ADD THIS

app = FastAPI(title="Power Trading System")
logger = get_logger("main")

# Root health check
@app.get("/")
def index():
    return {"status": "Power Trading System active (simulation mode)"}

# ✅ REGISTER ALL API ROUTES
app.include_router(router)
