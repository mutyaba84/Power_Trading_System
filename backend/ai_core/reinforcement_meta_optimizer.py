# backend/app/ai_core/reinforcement_meta_optimizer.py
"""
Reinforcement Meta Optimizer — Power Trading System

Purpose:
- Provide a stable "meta" layer that adapts RL/strategy hyperparameters over time
  based on observed performance and regime signals.
- Must be controller + LiveTrader compatible.
- Must NOT throw if fields are missing; operate safely with partial telemetry.

What this does (pragmatic, production-safe):
- Maintains an exponentially-weighted performance score (Sharpe-like, drawdown, winrate proxy)
- Adjusts exploration rate (epsilon), learning rate, and risk appetite factors within bounds
- Provides suggested parameter updates to RL agents or strategy optimizer

This is not a heavy ML optimizer; it's a robust online heuristic meta-controller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
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


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    if b == 0.0 or not math.isfinite(b):
        return default
    v = a / b
    return v if math.isfinite(v) else default


@dataclass
class MetaOptConfig:
    # EWM smoothing for statistics
    alpha_perf: float = 0.05          # performance EWMA
    alpha_risk: float = 0.05          # risk EWMA
    alpha_regime: float = 0.05        # regime EWMA

    # bounds for suggested params
    epsilon_min: float = 0.01
    epsilon_max: float = 0.30

    lr_min: float = 1e-5
    lr_max: float = 5e-3

    risk_min: float = 0.25            # risk appetite multiplier (position sizing / aggressiveness)
    risk_max: float = 1.75

    # adjustment sensitivities
    perf_sensitivity: float = 0.20    # how much performance shifts drive changes
    risk_sensitivity: float = 0.30    # how much risk/drawdown shifts drive changes
    regime_sensitivity: float = 0.15  # how much volatility/regime shifts drive changes

    # target-like anchors
    target_dd: float = 0.10           # "acceptable" drawdown fraction
    target_vol: float = 0.02          # typical vol proxy (e.g. ATR%); adjust to your feed
    target_edge: float = 0.0          # neutral edge

    # gating
    min_steps_before_updates: int = 50
    update_interval_steps: int = 10

    # safety
    nan_guard: float = 1e-12


@dataclass
class MetaState:
    steps: int = 0
    last_update_step: int = 0

    perf_ewma: float = 0.0            # proxy for edge / return
    perf_var_ewma: float = 1e-6       # proxy for variability

    dd_ewma: float = 0.0              # drawdown fraction ewma
    vol_ewma: float = 0.0             # volatility proxy ewma

    win_ewma: float = 0.5             # winrate proxy (0..1)
    trade_rate_ewma: float = 0.0      # trade count per step ewma

    # suggested knobs (carry state)
    epsilon: float = 0.10
    learning_rate: float = 1e-3
    risk_appetite: float = 1.0

    last_ts: float = field(default_factory=lambda: time.time())


@dataclass
class MetaTelemetry:
    """
    One-step telemetry snapshot.

    Provide what you have; missing fields are okay.
    """
    reward: Optional[float] = None
    realized_pnl: Optional[float] = None
    equity: Optional[float] = None
    peak_equity: Optional[float] = None
    drawdown: Optional[float] = None       # fraction 0..1
    volatility: Optional[float] = None     # proxy (ATR% etc.)
    trade_count: int = 0
    was_win: Optional[bool] = None         # if you can mark step/trade as win
    ts: Optional[float] = None


class ReinforcementMetaOptimizer:
    """
    Online meta-controller that outputs suggested updates:

    returns:
      {
        "epsilon": ...,
        "learning_rate": ...,
        "risk_appetite": ...,
        "signals": {...},
      }

    It is up to downstream RL/strategy modules to consume these values.
    """

    def __init__(self, cfg: Optional[MetaOptConfig] = None) -> None:
        self.cfg = cfg or MetaOptConfig()
        self.state = MetaState()

    def reset(self) -> None:
        self.state = MetaState()

    def update(self, tel: MetaTelemetry) -> Dict[str, Any]:
        """
        Update internal statistics and (occasionally) produce new suggested parameters.
        Safe: never raises.
        """
        cfg = self.cfg
        st = self.state

        st.steps += 1
        ts = _to_float(tel.ts, default=0.0) or time.time()
        st.last_ts = ts

        # ---- performance proxy ----
        # Prefer reward, else realized pnl, else 0
        perf = _to_float(tel.reward, default=0.0)
        if perf == 0.0:
            perf = _to_float(tel.realized_pnl, default=0.0)

        # EWMA of perf and perf variance (Welford-ish EWMA)
        delta = perf - st.perf_ewma
        st.perf_ewma = st.perf_ewma + cfg.alpha_perf * delta
        st.perf_var_ewma = (1.0 - cfg.alpha_perf) * st.perf_var_ewma + cfg.alpha_perf * (delta * delta)
        st.perf_var_ewma = max(st.perf_var_ewma, cfg.nan_guard)

        # "Sharpe-like" = mean / std
        perf_std = math.sqrt(st.perf_var_ewma)
        sharpe_like = _safe_div(st.perf_ewma, perf_std, default=0.0)

        # ---- risk proxies ----
        dd = _to_float(tel.drawdown, default=float("nan"))
        if not math.isfinite(dd):
            # compute if possible
            equity = _to_float(tel.equity, default=float("nan"))
            peak = _to_float(tel.peak_equity, default=float("nan"))
            if math.isfinite(equity) and math.isfinite(peak) and peak > 0.0:
                dd = _clamp((peak - equity) / peak, 0.0, 1.0)
            else:
                dd = 0.0
        dd = _clamp(dd, 0.0, 1.0)
        st.dd_ewma = st.dd_ewma + cfg.alpha_risk * (dd - st.dd_ewma)

        vol = _to_float(tel.volatility, default=0.0)
        vol = max(0.0, vol)
        st.vol_ewma = st.vol_ewma + cfg.alpha_regime * (vol - st.vol_ewma)

        # ---- behavior proxies ----
        tc = int(tel.trade_count or 0)
        st.trade_rate_ewma = st.trade_rate_ewma + cfg.alpha_regime * (tc - st.trade_rate_ewma)

        if tel.was_win is None:
            # infer win from perf sign
            win = 1.0 if perf > 0.0 else 0.0 if perf < 0.0 else st.win_ewma
        else:
            win = 1.0 if bool(tel.was_win) else 0.0
        st.win_ewma = st.win_ewma + cfg.alpha_perf * (win - st.win_ewma)

        # ---- decide if we should emit updates ----
        should_update = (
            st.steps >= cfg.min_steps_before_updates
            and (st.steps - st.last_update_step) >= cfg.update_interval_steps
        )

        if should_update:
            st.last_update_step = st.steps
            self._apply_meta_adjustments(sharpe_like=sharpe_like)

        return {
            "epsilon": st.epsilon,
            "learning_rate": st.learning_rate,
            "risk_appetite": st.risk_appetite,
            "signals": {
                "steps": st.steps,
                "perf_ewma": st.perf_ewma,
                "perf_std_ewma": perf_std,
                "sharpe_like": sharpe_like,
                "dd_ewma": st.dd_ewma,
                "vol_ewma": st.vol_ewma,
                "win_ewma": st.win_ewma,
                "trade_rate_ewma": st.trade_rate_ewma,
            },
        }

    def _apply_meta_adjustments(self, sharpe_like: float) -> None:
        """
        Heuristic parameter tuning:
        - If performance is strong and risk controlled, reduce exploration, slightly increase risk appetite.
        - If drawdown is rising or volatility spikes, increase exploration a bit (avoid getting stuck),
          decrease risk appetite, and reduce learning rate slightly for stability.
        """
        cfg = self.cfg
        st = self.state

        # Normalize "edge" from sharpe_like into [-1, 1] gently
        edge = math.tanh(sharpe_like / 2.0)  # stable squashing
        edge_delta = edge - cfg.target_edge

        dd_pressure = (st.dd_ewma - cfg.target_dd)  # positive means too much drawdown
        vol_pressure = (st.vol_ewma - cfg.target_vol)

        # Exploration: decrease with positive edge, increase if dd/vol pressure
        eps = st.epsilon
        eps += (-cfg.perf_sensitivity * edge_delta)
        eps += (cfg.risk_sensitivity * dd_pressure)
        eps += (cfg.regime_sensitivity * _clamp(vol_pressure / max(cfg.target_vol, cfg.nan_guard), -1.0, 1.0))
        eps = _clamp(eps, cfg.epsilon_min, cfg.epsilon_max)

        # Learning rate: increase a touch with good edge, decrease with risk/vol pressure
        lr = st.learning_rate
        lr *= (1.0 + 0.10 * cfg.perf_sensitivity * edge_delta)
        lr *= (1.0 - 0.20 * cfg.risk_sensitivity * _clamp(dd_pressure / max(cfg.target_dd, cfg.nan_guard), -1.0, 1.0))
        lr *= (1.0 - 0.10 * cfg.regime_sensitivity * _clamp(vol_pressure / max(cfg.target_vol, cfg.nan_guard), -1.0, 1.0))
        lr = _clamp(lr, cfg.lr_min, cfg.lr_max)

        # Risk appetite: increase with edge, decrease with drawdown/vol pressure and overtrading
        risk = st.risk_appetite
        risk += (0.25 * cfg.perf_sensitivity * edge_delta)
        risk -= (0.50 * cfg.risk_sensitivity * _clamp(dd_pressure / max(cfg.target_dd, cfg.nan_guard), -1.0, 1.0))
        risk -= (0.15 * cfg.regime_sensitivity * _clamp(vol_pressure / max(cfg.target_vol, cfg.nan_guard), -1.0, 1.0))

        # Penalize high trade-rate slightly (reduce aggression)
        trade_pressure = _clamp(st.trade_rate_ewma / 5.0, 0.0, 1.0)  # 5 fills/step = "high"
        risk -= 0.10 * trade_pressure

        risk = _clamp(risk, cfg.risk_min, cfg.risk_max)

        st.epsilon = eps
        st.learning_rate = lr
        st.risk_appetite = risk

    # Convenience adapter: accept dicts without forcing callers to import MetaTelemetry
    def update_from_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        tel = MetaTelemetry(
            reward=d.get("reward"),
            realized_pnl=d.get("realized_pnl"),
            equity=d.get("equity"),
            peak_equity=d.get("peak_equity"),
            drawdown=d.get("drawdown"),
            volatility=d.get("volatility"),
            trade_count=int(d.get("trade_count") or 0),
            was_win=d.get("was_win"),
            ts=d.get("ts"),
        )
        return self.update(tel)
