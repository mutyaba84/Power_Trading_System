"""
Power Trading System – backend entry point
Runs the FastAPI server and routes core operations.
"""
from fastapi import FastAPI
from backend.utils.logger import get_logger   # ✅ FIXED IMPORT

app = FastAPI(title="Power Trading System")
logger = get_logger("main")

@app.get("/")
def index():
    return {"status": "Power Trading System active (simulation mode)"}
