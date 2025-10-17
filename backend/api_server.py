from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_core.memory_manager import MemoryManager
from risk_manager import RiskManager
import psutil, json

app = FastAPI(title="Power Trading System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = MemoryManager()
risk = RiskManager()

@app.get("/status")
def get_status():
    return {
        "equity": risk.equity,
        "risk_limit": risk.max_drawdown,
        "free_memory_gb": psutil.virtual_memory().available / (1024**3)
    }

@app.get("/logs")
def get_logs():
    events = []
    for f in memory.external_dir.glob("*.json"):
        try:
            events.extend(json.loads(f.read_text()))
        except: pass
    return {"events": events[-50:]}  # latest 50
