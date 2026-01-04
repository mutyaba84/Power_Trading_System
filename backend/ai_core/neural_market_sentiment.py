# File: backend/ai_core/neural_market_sentiment.py
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _external_memory_root() -> Path:
    import os

    override = os.getenv("EXTERNAL_MEMORY")
    if override:
        return Path(override).expanduser().resolve()
    return (_project_root() / "external_memory").resolve()


def _safe_read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


class NeuralMarketSentiment:
    """
    Lightweight sentiment stub (no heavy ML deps) that:
      - estimates volatility from recent returns if provided
      - generates a stable mood + confidence output for the UI

    Writes: external_memory/ai_state/sentiment_state.json
    """

    def __init__(self) -> None:
        self.root = _external_memory_root()
        self.ai_state = self.root / "ai_state"
        self.ai_state.mkdir(parents=True, exist_ok=True)

        self.out_path = self.ai_state / "sentiment_state.json"

    def infer(
        self,
        *,
        price: Optional[float] = None,
        prev_price: Optional[float] = None,
        source: str = "dummy_market_feed",
    ) -> Dict[str, Any]:
        # basic return + volatility proxy
        ret = 0.0
        if price is not None and prev_price not in (None, 0):
            try:
                ret = (float(price) - float(prev_price)) / float(prev_price)
            except Exception:
                ret = 0.0

        # volatility proxy (bounded)
        volatility = min(0.99, max(0.0, abs(ret) * 25.0 + random.uniform(0.05, 0.15)))

        # mood heuristic
        if ret > 0.0005:
            mood = "bullish"
        elif ret < -0.0005:
            mood = "bearish"
        else:
            mood = "neutral"

        # confidence heuristic
        confidence = 0.55
        if mood != "neutral":
            confidence = min(0.90, 0.55 + abs(ret) * 120.0)
        # if volatility too high, confidence drops
        confidence = max(0.20, confidence * (1.0 - min(0.60, volatility * 0.35)))

        payload = {
            "timestamp": time.time(),
            "market_mood": mood,
            "confidence": round(float(confidence), 4),
            "volatility": round(float(volatility), 4),
            "source": source,
        }

        _safe_write_json(self.out_path, payload)
        return payload

    def read_last(self) -> Dict[str, Any]:
        return _safe_read_json(self.out_path)
