import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.ai_core.memory_manager import MemoryManager

app = FastAPI(title="Power Trading System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
AI_STATE_DIR = os.getenv("AI_STORAGE_PATH", "external_memory/ai_state")

# ✅ INITIALIZE MEMORY MANAGER (CRITICAL)
memory = MemoryManager(
    base_path="external_memory"
)

# --------------------------------------------------
# LOGS ENDPOINT
# --------------------------------------------------
@app.get("/logs")
def get_logs(limit: int = 50):
    """
    Return latest system events from external memory logs.
    Safe for frontend consumption.
    """
    events = []

    if not memory.external_dir.exists():
        return {"count": 0, "events": []}

    for f in sorted(memory.external_dir.glob("*.json"), reverse=True):
        try:
            content = json.loads(f.read_text())

            if isinstance(content, list):
                for event in content:
                    if isinstance(event, dict):
                        events.append(event)

        except Exception as e:
            print(f"[LOG READ ERROR] {f.name}: {e}")

        if len(events) >= limit:
            break

    return {
        "count": min(len(events), limit),
        "events": events[:limit]
    }

# --------------------------------------------------
# SENTIMENT ENDPOINT
# --------------------------------------------------
@app.get("/ai/sentiment")
def get_sentiment():
    """
    Return latest market sentiment snapshot.
    """
    path = os.path.join(AI_STATE_DIR, "sentiment_state.json")

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[SENTIMENT READ ERROR]: {e}")
        return {}
