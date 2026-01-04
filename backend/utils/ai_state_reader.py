import json
from pathlib import Path
from typing import Optional, Dict, Any

# Resolve project root reliably
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Single source of truth for AI state
AI_STATE_DIR = PROJECT_ROOT / "external_memory" / "ai_state"


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_sentiment_state() -> Optional[Dict[str, Any]]:
    return _read_json(AI_STATE_DIR / "sentiment_state.json")


def get_decision_state() -> Optional[Dict[str, Any]]:
    return _read_json(AI_STATE_DIR / "decision_kernel_state.json")


def get_paper_trading_state() -> Optional[Dict[str, Any]]:
    return _read_json(AI_STATE_DIR / "paper_trading_state.json")
