"""
Power Trading System – backend entry point
Runs the FastAPI server and routes core operations.
"""
from fastapi import FastAPI
from utils.logger import get_logger

app = FastAPI(title="Power Trading System")
logger = get_logger("main")

@app.get("/")
def index():
    return {"status": "Power Trading System active (simulation mode)"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting backend API...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
