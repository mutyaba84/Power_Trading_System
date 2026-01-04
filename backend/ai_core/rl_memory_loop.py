# backend/app/ai_core/rl_memory_loop.py
"""
RL Memory Loop — Power Trading System

Purpose:
- Provide a robust experience buffer + sampling interface for RL-ish components.
- Compatible with controller + LiveTrader.
- Safe with partial inputs; never raises on missing fields.
- Supports:
  * append(step) where step is a dict-like experience
  * sample(batch_size) returning a list of experiences
  * optional prioritized sampling (simple, stable)
  * persistence helpers (to_dict/from_dict) without file I/O

Experience schema (flexible):
{
  "ts": float,
  "state": Any,           # vector/list/dict (your encoder decides)
  "action": Any,          # int/str/dict
  "reward": float,
  "next_state": Any,
  "done": bool,
  "info": dict,           # optional extras (pnl, risk, etc.)
  "priority": float,      # optional for prioritized replay
}

This module does not assume numpy/torch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import math
import random
import time
from collections import deque


def _to_float(x: Any, default: float = 0.0) -> float:
    if x is None:
        return default
    if isinstance(x, (int, float)):
        try:
            v = float(x)
            return v if math.isfinite(v) else default
        except Exception:
            return default
    try:
        v = float(str(x).strip())
        return v if math.isfinite(v) else default
    except Exception:
        return default


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


@dataclass
class MemoryConfig:
    capacity: int = 50_000
    seed: Optional[int] = None

    # Prioritized replay (simple)
    prioritized: bool = False
    priority_alpha: float = 0.6     # how strongly priorities affect sampling (0=uniform)
    priority_eps: float = 1e-6      # avoid zero priority
    max_priority: float = 10.0      # cap

    # Safety
    min_ready: int = 200            # minimum experiences before "ready"


@dataclass
class MemoryStats:
    size: int = 0
    added: int = 0
    sampled: int = 0
    dropped: int = 0
    last_ts: float = field(default_factory=lambda: 0.0)


class RLMemoryLoop:
    """
    Deque-based replay buffer with optional prioritized sampling.
    """

    def __init__(self, cfg: Optional[MemoryConfig] = None) -> None:
        self.cfg = cfg or MemoryConfig()
        if self.cfg.seed is not None:
            random.seed(self.cfg.seed)

        self._buf: deque = deque(maxlen=max(1, int(self.cfg.capacity)))
        self._prio: deque = deque(maxlen=max(1, int(self.cfg.capacity)))  # mirror priorities if prioritized
        self.stats = MemoryStats()

    def reset(self) -> None:
        self._buf.clear()
        self._prio.clear()
        self.stats = MemoryStats()

    def __len__(self) -> int:
        return len(self._buf)

    def ready(self) -> bool:
        return len(self._buf) >= max(1, int(self.cfg.min_ready))

    def append(self, exp: Dict[str, Any]) -> None:
        """
        Append one experience. Never raises. Coerces minimal fields.
        """
        try:
            ts = _to_float(exp.get("ts"), default=0.0) or time.time()
            reward = _to_float(exp.get("reward"), default=0.0)
            done = bool(exp.get("done", False))

            normalized = {
                "ts": ts,
                "state": exp.get("state"),
                "action": exp.get("action"),
                "reward": reward,
                "next_state": exp.get("next_state"),
                "done": done,
                "info": exp.get("info") if isinstance(exp.get("info"), dict) else {},
            }

            # track drop count if deque is full (we can detect by length at cap)
            was_full = len(self._buf) == self._buf.maxlen

            self._buf.append(normalized)

            if self.cfg.prioritized:
                p = _to_float(exp.get("priority"), default=abs(reward))
                p = abs(p) + self.cfg.priority_eps
                p = _clamp(p, self.cfg.priority_eps, self.cfg.max_priority)
                self._prio.append(p)

            self.stats.size = len(self._buf)
            self.stats.added += 1
            self.stats.last_ts = ts
            if was_full and len(self._buf) == self._buf.maxlen:
                # if full before append, one element was dropped
                self.stats.dropped += 1
        except Exception:
            # swallow any malformed experience
            return

    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        Sample a batch. If not enough, returns as many as available.
        """
        n = len(self._buf)
        if n == 0:
            return []

        bs = max(1, int(batch_size))
        bs = min(bs, n)

        if not self.cfg.prioritized or len(self._prio) != n:
            batch = random.sample(list(self._buf), k=bs) if bs < n else list(self._buf)
            self.stats.sampled += bs
            return batch

        # prioritized sampling
        # weights = p^alpha
        alpha = _clamp(self.cfg.priority_alpha, 0.0, 1.0)
        weights = [max(self.cfg.priority_eps, float(p)) ** alpha for p in self._prio]
        total_w = sum(weights)
        if total_w <= 0.0 or not math.isfinite(total_w):
            # fallback to uniform
            batch = random.sample(list(self._buf), k=bs) if bs < n else list(self._buf)
            self.stats.sampled += bs
            return batch

        # sample indices via roulette
        indices = self._weighted_choice_indices(weights, k=bs)
        buf_list = list(self._buf)
        batch = [buf_list[i] for i in indices]

        self.stats.sampled += bs
        return batch

    def _weighted_choice_indices(self, weights: List[float], k: int) -> List[int]:
        """
        Weighted sampling without replacement (stable enough for moderate sizes).
        """
        # Copy weights so we can zero out chosen ones
        w = list(weights)
        idxs: List[int] = []

        for _ in range(k):
            total = sum(w)
            if total <= 0.0:
                break
            r = random.random() * total
            acc = 0.0
            chosen = 0
            for i, wi in enumerate(w):
                acc += wi
                if acc >= r:
                    chosen = i
                    break
            idxs.append(chosen)
            w[chosen] = 0.0  # no replacement

        # If we didn't get enough (due to numerical), fill uniformly from remaining
        if len(idxs) < k:
            remaining = [i for i in range(len(weights)) if i not in set(idxs)]
            if remaining:
                need = k - len(idxs)
                extra = random.sample(remaining, k=min(need, len(remaining)))
                idxs.extend(extra)

        return idxs

    def update_priorities(self, indices: List[int], priorities: List[float]) -> None:
        """
        Optional: update priorities after learning (TD error etc.).
        Indices should correspond to positions in the buffer list at sample time.
        Safe: ignores invalid indices.
        """
        if not self.cfg.prioritized:
            return
        if len(self._prio) != len(self._buf):
            return
        try:
            prio_list = list(self._prio)
            for i, p in zip(indices, priorities):
                if 0 <= i < len(prio_list):
                    pv = abs(_to_float(p, default=0.0)) + self.cfg.priority_eps
                    pv = _clamp(pv, self.cfg.priority_eps, self.cfg.max_priority)
                    prio_list[i] = pv
            self._prio = deque(prio_list, maxlen=self._buf.maxlen)
        except Exception:
            return

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize buffer (no file I/O).
        """
        return {
            "cfg": {
                "capacity": self.cfg.capacity,
                "seed": self.cfg.seed,
                "prioritized": self.cfg.prioritized,
                "priority_alpha": self.cfg.priority_alpha,
                "priority_eps": self.cfg.priority_eps,
                "max_priority": self.cfg.max_priority,
                "min_ready": self.cfg.min_ready,
            },
            "stats": {
                "size": self.stats.size,
                "added": self.stats.added,
                "sampled": self.stats.sampled,
                "dropped": self.stats.dropped,
                "last_ts": self.stats.last_ts,
            },
            "buffer": list(self._buf),
            "priorities": list(self._prio) if self.cfg.prioritized else [],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RLMemoryLoop":
        cfg_d = d.get("cfg") or {}
        cfg = MemoryConfig(
            capacity=int(cfg_d.get("capacity", 50_000)),
            seed=cfg_d.get("seed"),
            prioritized=bool(cfg_d.get("prioritized", False)),
            priority_alpha=_to_float(cfg_d.get("priority_alpha"), 0.6),
            priority_eps=_to_float(cfg_d.get("priority_eps"), 1e-6),
            max_priority=_to_float(cfg_d.get("max_priority"), 10.0),
            min_ready=int(cfg_d.get("min_ready", 200)),
        )
        obj = cls(cfg=cfg)

        buf = d.get("buffer") or []
        for exp in buf:
            if isinstance(exp, dict):
                obj.append(exp)

        # restore priorities if present and prioritized
        if obj.cfg.prioritized:
            prios = d.get("priorities") or []
            # If we have equal lengths, use those priorities, else keep auto priorities from append()
            if isinstance(prios, list) and len(prios) == len(obj._buf):
                obj._prio = deque(
                    [_clamp(abs(_to_float(p, obj.cfg.priority_eps)) + obj.cfg.priority_eps,
                            obj.cfg.priority_eps, obj.cfg.max_priority) for p in prios],
                    maxlen=obj._buf.maxlen,
                )

        stats_d = d.get("stats") or {}
        try:
            obj.stats.size = len(obj._buf)
            obj.stats.added = int(stats_d.get("added", obj.stats.added))
            obj.stats.sampled = int(stats_d.get("sampled", obj.stats.sampled))
            obj.stats.dropped = int(stats_d.get("dropped", obj.stats.dropped))
            obj.stats.last_ts = _to_float(stats_d.get("last_ts"), obj.stats.last_ts)
        except Exception:
            pass

        return obj
