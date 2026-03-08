# backend/routes/api_adapter.py
from __future__ import annotations

from fastapi import APIRouter
from typing import Any, Dict, List
import time

# Existing route handlers in your backend
from backend.routes.system import system_status as _status
from backend.routes.logs import logs as _logs
from backend.routes.ai import get_sentiment as _get_sentiment, get_decision as _get_decision
from backend.routes.controller import controller_start as _controller_start, controller_stop as _controller_stop

router = APIRouter(prefix="/api", tags=["api"])


def _now() -> int:
    return int(time.time())


def _merge_defaults(defaults: Dict[str, Any], incoming: Any) -> Dict[str, Any]:
    base = dict(defaults)

    if isinstance(incoming, dict):
        for k, v in incoming.items():
            if v is not None:
                base[k] = v

    if base.get("ts") is None:
        base["ts"] = _now()
    if base.get("raw") is None:
        base["raw"] = {}

    return base


def _ensure_useful_raw(merged: Dict[str, Any]) -> Dict[str, Any]:
    raw = merged.get("raw")
    if not isinstance(raw, dict) or len(raw) == 0:
        snap = dict(merged)
        snap.pop("raw", None)
        merged["raw"] = snap
    return merged


def _sentiment_defaults() -> Dict[str, Any]:
    return {
        "confidence": 0.0,
        "volatility": 0.0,
        "positive": 0.0,
        "negative": 0.0,
        "neutral": 1.0,
        "mood": "unknown",
        "market_mood": None,
        "source": None,
        "timestamp": None,  # float seconds if provided by upstream
        "vix": None,
        "raw": {},
        "ts": _now(),
    }


def _decision_defaults() -> Dict[str, Any]:
    return {
        "action": "HOLD",
        "action_score": 0.0,
        "scaled_confidence": 0.0,
        "fusion_output": {},
        "quantum_expected": 0.0,
        "quantum_uncertainty": 0.0,
        "source": None,
        "timestamp": None,
        "raw": {},
        "ts": _now(),
    }


def _coerce_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        try:
            s = str(v).strip().replace(",", "")
            return float(s)
        except Exception:
            return None


def _coerce_ts(v):
    # Accept seconds or ms; return seconds int
    try:
        if v is None:
            return None
        f = float(v)
        if f > 1e12:
            return int(f / 1000.0)
        return int(f)
    except Exception:
        return None


@router.get("/status")
def api_status() -> Dict[str, Any]:
    defaults = {
        "status": "UNKNOWN",
        "timestamp": _now(),
        "free_memory_gb": None,
        "equity": None,
        "risk_limit": None,
        "raw": {},
        "ts": _now(),
    }
    try:
        data = _status()
        merged = _merge_defaults(defaults, data)
        if isinstance(data, dict):
            merged["raw"] = data
        return _ensure_useful_raw(merged)
    except Exception:
        merged = dict(defaults)
        merged["status"] = "OFFLINE"
        return _ensure_useful_raw(merged)


@router.get("/sentiment")
def api_sentiment() -> Dict[str, Any]:
    try:
        data = _get_sentiment()
        merged = _merge_defaults(_sentiment_defaults(), data)
        return _ensure_useful_raw(merged)
    except Exception:
        merged = _sentiment_defaults()
        return _ensure_useful_raw(merged)


@router.get("/decision/latest")
def api_decision_latest() -> Dict[str, Any]:
    try:
        data = _get_decision()
        merged = _merge_defaults(_decision_defaults(), data)
        return _ensure_useful_raw(merged)
    except Exception:
        merged = _decision_defaults()
        return _ensure_useful_raw(merged)


@router.get("/logs")
def api_logs(limit: int = 50) -> Dict[str, Any]:
    try:
        data = _logs(limit=limit)
        if isinstance(data, dict) and isinstance(data.get("events"), list):
            return data
        if isinstance(data, list):
            return {"events": data[:limit]}
        return {"events": []}
    except Exception:
        return {"events": []}


@router.get("/trades")
def api_trades() -> Dict[str, Any]:
    """
    Derive trades from structured log events (trade.registered).
    """
    try:
        data = _logs(limit=500)

        events: List[Any] = []
        if isinstance(data, dict) and isinstance(data.get("events"), list):
            events = data["events"]
        elif isinstance(data, list):
            events = data
        else:
            return {"trades": []}

        trades: List[Dict[str, Any]] = []

        for ev in events:
            if not isinstance(ev, dict):
                continue

            # ✅ Only real trade events
            if ev.get("event") != "trade.registered":
                continue

            action = ev.get("action")
            if not action:
                continue

            trades.append(
                {
                    "ts": _coerce_ts(ev.get("ts") or ev.get("timestamp")),
                    "action": str(action).upper(),
                    "size": _coerce_float(ev.get("size")),
                    "price": _coerce_float(ev.get("price")),
                    "pnl": _coerce_float(ev.get("pnl")),
                    "equity": _coerce_float(ev.get("equity")),
                }
            )

        return {"trades": trades}

    except Exception:
        return {"trades": []}

@router.post("/controller/start")
def api_controller_start() -> Dict[str, Any]:
    try:
        return _controller_start()
    except Exception:
        return {"ok": True, "ts": _now()}


@router.post("/controller/stop")
def api_controller_stop() -> Dict[str, Any]:
    try:
        return _controller_stop()
    except Exception:
        return {"ok": True, "ts": _now()}
