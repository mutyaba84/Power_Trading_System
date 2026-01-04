# backend/app/ai_core/reward_policy.py
"""
Reward Policy — Power Trading System

Goal:
- Provide a stable, controller/LiveTrader-compatible reward signal for RL-style components.
- Avoid brittle dependencies on any specific broker/exchange adapter.
- Be explicit, numerical, and safe (never throw on missing fields).

Design:
- Stateless compute() interface for single-step reward, plus an optional small state tracker for
  position/peak equity to compute drawdown penalties consistently across steps.
- Reward is a weighted sum of:
  * realized PnL (when a trade closes / realized component is available)
  * mark-to-market / unrealized delta (optional)
  * risk penalties (drawdown, volatility proxy, exposure)
  * behavioral penalties (overtrading, churn, flip-flopping, long holds)
  * execution penalties (fees, slippage)

This file is deliberately standalone: no imports from other project modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
import math
import time


def _to_float(x: Any, default: float = 0.0) -> float:
    """Best-effort numeric conversion; never raises."""
    if x is None:
        return default
    if isinstance(x, (int, float)) and math.isfinite(float(x)):
        return float(x)
    # common string numbers
    try:
        v = float(str(x).strip())
        return v if math.isfinite(v) else default
    except Exception:
        return default


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


@dataclass
class RewardConfig:
    # --- core scaling ---
    pnl_scale: float = 1.0                 # scales pnl terms into reward units
    reward_clip: float = 10.0              # final reward clamp to [-clip, clip]

    # --- pnl components ---
    use_realized_pnl: bool = True
    use_unrealized_pnl: bool = False       # if you have equity/mark-to-market changes
    realized_weight: float = 1.0
    unrealized_weight: float = 0.25

    # --- costs / execution ---
    fee_weight: float = 1.0               # penalty per unit fee (already in account currency)
    slippage_weight: float = 0.5          # penalty per unit slippage (account currency)
    spread_weight: float = 0.0            # optional

    # --- risk penalties ---
    drawdown_weight: float = 0.5          # penalty on drawdown fraction (0..1)
    exposure_weight: float = 0.15         # penalty on abs(position_notional)/equity
    volatility_weight: float = 0.0        # optional penalty if volatility proxy provided

    # --- behavior penalties ---
    trade_count_weight: float = 0.05      # penalty per trade (discourages overtrading)
    position_flip_weight: float = 0.1     # penalty when position sign flips
    hold_time_weight: float = 0.0         # penalty per second holding (optional)
    churn_weight: float = 0.05            # penalty for large position changes

    # --- normalization / safety ---
    min_equity: float = 1.0               # prevent divide-by-zero; also caps exposure explosions
    dd_epsilon: float = 1e-9              # stable drawdown computation


@dataclass
class RewardContext:
    """
    A single-step snapshot passed into RewardPolicy.compute().

    Provide what you have; missing fields default to safe values.

    Common producers:
    - LiveTrader loop each tick/bar
    - Controller after order fills
    """
    # account / equity
    equity: Optional[float] = None            # current equity
    prev_equity: Optional[float] = None       # equity from previous step (for unrealized delta)
    balance: Optional[float] = None           # optional

    # pnl
    realized_pnl: Optional[float] = None      # realized pnl for this step (closed trades)
    unrealized_pnl: Optional[float] = None    # optional mark-to-market pnl (current)
    pnl_delta: Optional[float] = None         # optional direct equity change if you compute it

    # execution costs
    fees: Optional[float] = None
    slippage: Optional[float] = None
    spread_cost: Optional[float] = None

    # position / exposure
    position_qty: Optional[float] = None      # signed position size (contracts/shares)
    position_notional: Optional[float] = None # signed notional in account currency
    price: Optional[float] = None             # current price, if notional needs derivation

    # behavioral signals
    trade_count: int = 0                      # number of fills this step
    position_change_notional: Optional[float] = None  # abs(delta notional) this step

    # risk proxy
    volatility: Optional[float] = None        # e.g. ATR%, stdev%, etc.

    # timing
    ts: Optional[float] = None                # unix timestamp seconds


@dataclass
class RewardBreakdown:
    total: float
    components: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, float]:
        d = dict(self.components)
        d["total"] = self.total
        return d


class RewardPolicy:
    """
    Stateful reward policy:
    - Tracks peak equity for drawdown.
    - Tracks previous position sign for flip penalty.
    - Tracks holding start time (optional) if you want hold-time penalty.
    """

    def __init__(self, cfg: Optional[RewardConfig] = None) -> None:
        self.cfg = cfg or RewardConfig()
        self.reset()

    def reset(self) -> None:
        self._peak_equity: float = 0.0
        self._last_equity: Optional[float] = None
        self._last_position_sign: int = 0
        self._hold_start_ts: Optional[float] = None
        self._last_position_notional: float = 0.0

    def compute(self, ctx: RewardContext) -> Tuple[float, RewardBreakdown]:
        cfg = self.cfg

        # --- equity resolution ---
        equity = _to_float(ctx.equity, default=0.0)
        prev_equity = _to_float(ctx.prev_equity, default=0.0)

        if equity <= 0.0 and self._last_equity is not None:
            equity = float(self._last_equity)

        equity_safe = max(equity, cfg.min_equity)

        # update peak equity for drawdown calc
        if self._peak_equity <= 0.0:
            # initialize peak to first observed equity
            if equity > 0.0:
                self._peak_equity = equity
        else:
            if equity > self._peak_equity:
                self._peak_equity = equity

        peak_safe = max(self._peak_equity, cfg.min_equity)

        # --- pnl terms ---
        realized = _to_float(ctx.realized_pnl, default=0.0)
        unrealized = _to_float(ctx.unrealized_pnl, default=0.0)

        # If pnl_delta provided, it can stand in for unrealized delta reward
        pnl_delta = _to_float(ctx.pnl_delta, default=0.0)
        if pnl_delta == 0.0 and equity > 0.0 and prev_equity > 0.0:
            pnl_delta = equity - prev_equity

        pnl_term = 0.0
        comps: Dict[str, float] = {}

        if cfg.use_realized_pnl:
            r = cfg.realized_weight * realized
            pnl_term += r
            comps["realized_pnl"] = r

        if cfg.use_unrealized_pnl:
            u = cfg.unrealized_weight * unrealized
            pnl_term += u
            comps["unrealized_pnl"] = u
        else:
            # optional "equity delta" shaping without depending on unrealized field
            if pnl_delta != 0.0:
                u = cfg.unrealized_weight * pnl_delta
                pnl_term += u
                comps["equity_delta"] = u

        pnl_term *= cfg.pnl_scale

        # --- costs ---
        fees = _to_float(ctx.fees, default=0.0)
        slippage = _to_float(ctx.slippage, default=0.0)
        spread_cost = _to_float(ctx.spread_cost, default=0.0)

        cost_pen = (
            cfg.fee_weight * fees
            + cfg.slippage_weight * slippage
            + cfg.spread_weight * spread_cost
        )
        if cost_pen != 0.0:
            comps["costs"] = -abs(cost_pen) * cfg.pnl_scale

        # --- exposure penalty ---
        pos_notional = _to_float(ctx.position_notional, default=0.0)

        # attempt derive notional if qty + price is given
        if pos_notional == 0.0:
            qty = _to_float(ctx.position_qty, default=0.0)
            price = _to_float(ctx.price, default=0.0)
            if qty != 0.0 and price > 0.0:
                pos_notional = qty * price

        exposure_frac = abs(pos_notional) / equity_safe
        exposure_pen = cfg.exposure_weight * exposure_frac
        if exposure_pen != 0.0:
            comps["exposure"] = -exposure_pen

        # --- drawdown penalty ---
        # drawdown fraction from peak equity
        dd = (peak_safe - equity_safe) / max(peak_safe, cfg.dd_epsilon)
        dd = _clamp(dd, 0.0, 1.0)
        dd_pen = cfg.drawdown_weight * dd
        if dd_pen != 0.0:
            comps["drawdown"] = -dd_pen

        # --- volatility penalty (optional proxy) ---
        vol = _to_float(ctx.volatility, default=0.0)
        vol_pen = cfg.volatility_weight * max(0.0, vol)
        if vol_pen != 0.0:
            comps["volatility"] = -vol_pen

        # --- behavior penalties ---
        trade_count = int(ctx.trade_count or 0)
        if trade_count > 0 and cfg.trade_count_weight != 0.0:
            comps["overtrade"] = -cfg.trade_count_weight * trade_count

        # position flip penalty
        pos_sign = 0
        if pos_notional > 0:
            pos_sign = 1
        elif pos_notional < 0:
            pos_sign = -1

        if self._last_position_sign != 0 and pos_sign != 0 and pos_sign != self._last_position_sign:
            if cfg.position_flip_weight != 0.0:
                comps["flip"] = -cfg.position_flip_weight

        # churn penalty: penalize large changes in notional exposure (abs delta / equity)
        d_notional = _to_float(ctx.position_change_notional, default=0.0)
        if d_notional == 0.0:
            d_notional = abs(pos_notional - self._last_position_notional)
        churn_frac = abs(d_notional) / equity_safe
        churn_pen = cfg.churn_weight * churn_frac
        if churn_pen != 0.0:
            comps["churn"] = -churn_pen

        # hold-time penalty (optional): penalize holding any position for long times
        ts = _to_float(ctx.ts, default=0.0) or time.time()
        if pos_sign == 0:
            self._hold_start_ts = None
        else:
            if self._hold_start_ts is None:
                self._hold_start_ts = ts

        hold_pen = 0.0
        if cfg.hold_time_weight != 0.0 and self._hold_start_ts is not None:
            held_secs = max(0.0, ts - self._hold_start_ts)
            hold_pen = cfg.hold_time_weight * held_secs
            if hold_pen != 0.0:
                comps["hold_time"] = -hold_pen

        # --- total reward ---
        reward = pnl_term
        # subtract costs and penalties
        reward += comps.get("costs", 0.0)
        reward += comps.get("exposure", 0.0)
        reward += comps.get("drawdown", 0.0)
        reward += comps.get("volatility", 0.0)
        reward += comps.get("overtrade", 0.0)
        reward += comps.get("flip", 0.0)
        reward += comps.get("churn", 0.0)
        reward += comps.get("hold_time", 0.0)

        # clip for stability
        reward = _clamp(reward, -cfg.reward_clip, cfg.reward_clip)

        # --- update internal state ---
        if equity > 0.0:
            self._last_equity = equity
        self._last_position_sign = pos_sign
        self._last_position_notional = pos_notional

        return reward, RewardBreakdown(total=reward, components=comps)

    # Convenience adapter: accept dicts without forcing callers to import RewardContext
    def compute_from_dict(self, d: Dict[str, Any]) -> Tuple[float, RewardBreakdown]:
        ctx = RewardContext(
            equity=d.get("equity"),
            prev_equity=d.get("prev_equity"),
            balance=d.get("balance"),
            realized_pnl=d.get("realized_pnl"),
            unrealized_pnl=d.get("unrealized_pnl"),
            pnl_delta=d.get("pnl_delta"),
            fees=d.get("fees"),
            slippage=d.get("slippage"),
            spread_cost=d.get("spread_cost"),
            position_qty=d.get("position_qty"),
            position_notional=d.get("position_notional"),
            price=d.get("price"),
            trade_count=int(d.get("trade_count") or 0),
            position_change_notional=d.get("position_change_notional"),
            volatility=d.get("volatility"),
            ts=d.get("ts"),
        )
        return self.compute(ctx)
