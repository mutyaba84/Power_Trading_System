# backend/ai_core/learning_engine.py
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from backend.utils.logger import get_logger

logger = get_logger("LearningEngine")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _external_memory_root() -> Path:
    env = os.getenv("EXTERNAL_MEMORY")
    if env:
        return Path(env).expanduser().resolve()
    return (_project_root() / "external_memory").resolve()


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or isinstance(v, bool):
            return default
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            return float(v.strip())
        return float(v)
    except Exception:
        return default


# ---- Persistence hook (preferred) ----
# We prefer using backend.ai_core.utils.persistence if you created it.
# If it doesn't exist yet, we fallback to a minimal safe writer (best effort).
try:
    from backend.ai_core.utils.persistence import atomic_write_json as _atomic_write_json  # type: ignore
    from backend.ai_core.utils.persistence import ai_core_read_only as _ai_core_read_only  # type: ignore
except Exception:
    _atomic_write_json = None  # type: ignore

    def _ai_core_read_only() -> bool:
        v = os.getenv("AI_CORE_READ_ONLY", "true").strip().lower()
        return v in ("1", "true", "yes", "y", "on")


def _fallback_atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Best-effort atomic write if helper isn't available.
    NOTE: This does NOT include cross-process locking.
    It's only here so imports never fail; you should still add utils/persistence.py.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}.{int(time.time() * 1000)}")
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    with tmp.open("w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    try:
        tmp.replace(path)
    except Exception:
        # If replace fails, try direct write as last resort (avoid crashing LiveTrader)
        try:
            with path.open("w", encoding="utf-8") as f2:
                f2.write(payload)
                f2.flush()
                os.fsync(f2.fileno())
        except Exception:
            pass
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


class LearningEngine:
    """
    Stable scaffolding layer for LiveTrader and UI.

    Writes (ONLY if AI_CORE_READ_ONLY=false):
      - external_memory/ai_state/sentiment_state.json
      - external_memory/ai_state/decision_kernel_state.json
    """

    def __init__(self) -> None:
        self.mem_root = _external_memory_root()
        self.ai_state_dir = self.mem_root / "ai_state"
        self.ai_state_dir.mkdir(parents=True, exist_ok=True)

        self.sentiment_path = self.ai_state_dir / "sentiment_state.json"
        self.decision_path = self.ai_state_dir / "decision_kernel_state.json"

        self.graph = None
        self.memory = None

        self._last_persist_ts = 0.0
        self._persist_every_s = float(os.getenv("AI_STATE_PERSIST_EVERY_S", "0.5"))

        self._trade_count = 0
        self._pnl_sum = 0.0

        self._try_init_optional()

        # initial write (safe; skipped if read-only)
        try:
            self._persist_sentiment(self._default_sentiment())
            self._persist_decision(self._default_decision())
        except Exception as e:
            logger.warning(f"Failed writing initial ai_state (ok): {e}")

        logger.info(f"LearningEngine ready. ai_state_dir={self.ai_state_dir} read_only={_ai_core_read_only()}")

    def _try_init_optional(self) -> None:
        try:
            from backend.ai_core.knowledge_graph import KnowledgeGraph  # type: ignore

            self.graph = KnowledgeGraph()
            logger.info("KnowledgeGraph loaded.")
        except Exception as e:
            self.graph = None
            logger.warning(f"KnowledgeGraph unavailable (ok): {e}")

        try:
            from backend.ai_core.memory_manager import MemoryManager  # type: ignore

            self.memory = MemoryManager()
            logger.info("MemoryManager loaded.")
        except Exception as e:
            self.memory = None
            logger.warning(f"MemoryManager unavailable (ok): {e}")

    # -------------------------
    # Public API used by trader
    # -------------------------

    def get_sentiment(self, tick: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        price = tick.get("price") if isinstance(tick, dict) else None
        volatility = _to_float(tick.get("volatility"), 0.48) if isinstance(tick, dict) else 0.48

        confidence = 0.60 + min(0.35, max(0.0, 0.20 - (volatility * 2.0)))
        mood = "bullish" if (price is None or _to_float(price, 100.0) >= 100.0) else "bearish"

        out = {
            "market_mood": mood,
            "confidence": round(float(confidence), 2),
            "volatility": round(float(volatility), 2),
            "source": "learning_engine",
            "timestamp": time.time(),
        }
        self._maybe_persist(out, which="sentiment")
        return out

    def decide(self, tick: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sentiment = self.get_sentiment(tick)
        conf = _to_float(sentiment.get("confidence"), 0.7)
        mood = str(sentiment.get("market_mood", "neutral"))

        if conf >= 0.78 and mood == "bullish":
            decision = "buy"
        elif conf >= 0.78 and mood == "bearish":
            decision = "sell"
        else:
            decision = "hold"

        out = {
            "decision": decision,
            "confidence": round(conf, 2),
            "strategy": "heuristic_v1",
            "timestamp": time.time(),
        }
        self._maybe_persist(out, which="decision")
        return out

    def reinforce(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        action = None
        pnl = 0.0
        confidence = 0.0
        tick: Optional[Dict[str, Any]] = None
        meta: Dict[str, Any] = {}

        if "action" in kwargs:
            action = kwargs.get("action")
        if "pnl" in kwargs:
            pnl = _to_float(kwargs.get("pnl"), 0.0)
        if "confidence" in kwargs:
            confidence = _to_float(kwargs.get("confidence"), 0.0)
        if "tick" in kwargs and isinstance(kwargs.get("tick"), dict):
            tick = kwargs.get("tick")
        if "meta" in kwargs and isinstance(kwargs.get("meta"), dict):
            meta.update(kwargs.get("meta"))

        if args:
            if action is None:
                action = args[0]

            for v in args[1:]:
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    pnl = float(v)
                    break

            dicts = [v for v in args if isinstance(v, dict)]
            if dicts:
                if tick is None:
                    tick = dicts[0]
                for d in dicts[1:]:
                    meta.update(d)

            for v in args[1:]:
                if isinstance(v, str) and v.strip() and v.strip().lower() not in ("buy", "sell", "hold"):
                    meta.setdefault("tag", v.strip())

        action_str = str(action) if action is not None else "unknown"

        self._trade_count += 1
        self._pnl_sum += float(pnl)

        record = {
            "ts": time.time(),
            "action": action_str,
            "pnl": float(pnl),
            "confidence": float(confidence),
            "tick": tick if isinstance(tick, dict) else None,
            "meta": meta if isinstance(meta, dict) else None,
            "trade_count": int(self._trade_count),
            "pnl_sum": float(self._pnl_sum),
        }

        if self.memory is not None:
            try:
                if hasattr(self.memory, "append"):
                    self.memory.append(record)  # type: ignore
                elif hasattr(self.memory, "store"):
                    self.memory.store(record)  # type: ignore
                elif hasattr(self.memory, "remember"):
                    self.memory.remember(record)  # type: ignore
            except Exception as e:
                logger.warning(f"MemoryManager record failed (ok): {e}")

        if self.graph is not None:
            try:
                if hasattr(self.graph, "observe_trade"):
                    self.graph.observe_trade(record)  # type: ignore
                elif hasattr(self.graph, "add_event"):
                    self.graph.add_event("trade", record)  # type: ignore
            except Exception as e:
                logger.warning(f"KnowledgeGraph update failed (ok): {e}")

        # refresh UI state (safe)
        try:
            self.get_sentiment(tick)
            self.decide(tick)
        except Exception as e:
            logger.warning(f"State refresh failed (ok): {e}")

        return {"ok": True, "trade_count": self._trade_count, "pnl_sum": round(self._pnl_sum, 2)}

    # -------------------------
    # Persistence helpers
    # -------------------------

    def _maybe_persist(self, payload: Dict[str, Any], which: str) -> None:
        if _ai_core_read_only():
            return

        now = time.time()
        if (now - self._last_persist_ts) < self._persist_every_s:
            return
        self._last_persist_ts = now

        if which == "sentiment":
            self._persist_sentiment(payload)
        elif which == "decision":
            self._persist_decision(payload)

    def _persist_sentiment(self, payload: Dict[str, Any]) -> None:
        try:
            if _atomic_write_json is not None:
                _atomic_write_json(self.sentiment_path, payload)  # type: ignore
            else:
                _fallback_atomic_write_json(self.sentiment_path, payload)
        except Exception as e:
            logger.warning(f"Sentiment persist failed (ok): {e}")

    def _persist_decision(self, payload: Dict[str, Any]) -> None:
        try:
            if _atomic_write_json is not None:
                _atomic_write_json(self.decision_path, payload)  # type: ignore
            else:
                _fallback_atomic_write_json(self.decision_path, payload)
        except Exception as e:
            logger.warning(f"Decision persist failed (ok): {e}")

    # -------------------------
    # Defaults
    # -------------------------

    def _default_sentiment(self) -> Dict[str, Any]:
        return {
            "market_mood": "bullish",
            "confidence": 0.77,
            "volatility": 0.48,
            "source": "bootstrap",
            "timestamp": time.time(),
        }

    def _default_decision(self) -> Dict[str, Any]:
        return {
            "decision": "hold",
            "confidence": 0.70,
            "strategy": "bootstrap",
            "timestamp": time.time(),
        }
