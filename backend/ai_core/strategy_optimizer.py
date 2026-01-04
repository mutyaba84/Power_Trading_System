# backend/app/ai_core/strategy_optimizer.py
"""
Strategy Optimizer — Power Trading System

Purpose:
- Bridge between signals/AI outputs and concrete trading strategy parameters.
- Consume meta-optimizer outputs, reward feedback, and market context.
- Produce stable, bounded strategy parameters usable by LiveTrader / controller.

This module does NOT place trades.
It only suggests *how* strategies should behave (risk, sizing, thresholds, cooldowns).

Design goals:
- Fully deterministic, no randomness
- Safe with partial inputs
- No dependency on other ai_core internals
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import math
import time


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
class StrategyOptConfig:
    # Base defaults (neutral)
    base_risk: float = 1.0
    base_position_fraction: float = 0.02   # 2% of equity
    base_cooldown_sec: float = 5.0
    base_signal_threshold: float = 0.5     # generic confidence threshold

    # Bounds
    min_position_fraction: float = 0.002
    max_position_fraction: float = 0.10

    min_cooldown_sec: float = 0.0
    max_cooldown_sec: float = 120.0

    min_signal_threshold: float = 0.1
    max_signal_threshold: float = 0.9

    # Sensitivities
    risk_to_size: float = 0.75
    risk_to_threshold: float = 0.40
    vol_to_cooldown: float = 1.5
    dd_to_cooldown: float = 2.0

    # Safety
    nan_guard: float = 1e-9


@dataclass
class StrategyState:
    last_update_ts: float = field(default_factory=lambda: time.time())

    # Current suggested parameters
    position_fraction: float = 0.02
    cooldown_sec: float = 5.0
    signal_threshold: float = 0.5
    risk_multiplier: float = 1.0


class StrategyOptimizer:
    """
    Deterministic optimizer producing a *strategy parameter bundle*.

    Inputs (optional, dict-style):
    - meta: output from ReinforcementMetaOptimizer.update()
    - performance: reward / pnl summary
    - risk: drawdown, volatility
    """

    def __init__(self, cfg: Optional[StrategyOptConfig] = None) -> None:
        self.cfg = cfg or StrategyOptConfig()
        self.state = StrategyState(
            position_fraction=self.cfg.base_position_fraction,
            cooldown_sec=self.cfg.base_cooldown_sec,
            signal_threshold=self.cfg.base_signal_threshold,
            risk_multiplier=self.cfg.base_risk,
        )

    def reset(self) -> None:
        self.state = StrategyState(
            position_fraction=self.cfg.base_position_fraction,
            cooldown_sec=self.cfg.base_cooldown_sec,
            signal_threshold=self.cfg.base_signal_threshold,
            risk_multiplier=self.cfg.base_risk,
        )

    def update(self, payload: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute new strategy parameters.

        payload may include:
        {
          "meta": {...},            # epsilon, learning_rate, risk_appetite, signals
          "reward": float,
          "drawdown": float,
          "volatility": float,
          "ts": float
        }
        """
        cfg = self.cfg
        st = self.state

        meta = payload.get("meta") or {}
        risk_appetite = _to_float(meta.get("risk_appetite"), st.risk_multiplier)

        reward = _to_float(payload.get("reward"), 0.0)
        drawdown = _clamp(_to_float(payload.get("drawdown"), 0.0), 0.0, 1.0)
        volatility = max(0.0, _to_float(payload.get("volatility"), 0.0))

        # --- risk multiplier ---
        # Smooth risk appetite into usable multiplier
        risk_mult = _clamp(
            cfg.base_risk * risk_appetite,
            0.25,
            2.0,
        )

        # --- position sizing ---
        size = cfg.base_position_fraction
        size *= (1.0 + cfg.risk_to_size * (risk_mult - 1.0))

        # Penalize size under drawdown
        size *= (1.0 - 0.75 * drawdown)
        size = _clamp(size, cfg.min_position_fraction, cfg.max_position_fraction)

        # --- signal threshold ---
        # Higher risk appetite => accept weaker signals
        thresh = cfg.base_signal_threshold
        thresh -= cfg.risk_to_threshold * (risk_mult - 1.0)

        # If recent reward negative, demand stronger signals
        if reward < 0.0:
            thresh += min(0.15, abs(reward))

        thresh = _clamp(thresh, cfg.min_signal_threshold, cfg.max_signal_threshold)

        # --- cooldown ---
        cooldown = cfg.base_cooldown_sec

        # Increase cooldown under volatility and drawdown
        cooldown *= (1.0 + cfg.vol_to_cooldown * volatility)
        cooldown *= (1.0 + cfg.dd_to_cooldown * drawdown)

        cooldown = _clamp(cooldown, cfg.min_cooldown_sec, cfg.max_cooldown_sec)

        # --- update state ---
        ts = _to_float(payload.get("ts"), default=0.0) or time.time()
        st.last_update_ts = ts
        st.position_fraction = size
        st.cooldown_sec = cooldown
        st.signal_threshold = thresh
        st.risk_multiplier = risk_mult

        return {
            "position_fraction": size,
            "cooldown_sec": cooldown,
            "signal_threshold": thresh,
            "risk_multiplier": risk_mult,
        }
