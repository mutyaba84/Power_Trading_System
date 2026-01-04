import json
from pathlib import Path
from fastapi import APIRouter

from backend.utils.event_log import log_request
from backend.utils.paths import ai_state_dir

router = APIRouter()

# Centralized, stable AI state directory
AI_STATE: Path = ai_state_dir()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@router.get("/sentiment")
@log_request(
    "ai.sentiment",
    include_fields=[
        "market_mood",
        "confidence",
        "volatility",
        "source",
        "timestamp",
    ],
)
def get_sentiment():
    return _read_json(AI_STATE / "sentiment_state.json")


@router.get("/decision")
@log_request(
    "ai.decision",
    include_fields=[
        "decision",
        "confidence",
        "strategy",
        "timestamp",
    ],
)
def get_decision():
    return _read_json(AI_STATE / "decision_kernel_state.json")
