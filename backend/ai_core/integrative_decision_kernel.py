# File: backend/ai_core/integrative_decision_kernel.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


def _project_root() -> Path:
    # backend/ai_core -> backend -> project root
    return Path(__file__).resolve().parents[2]


def _external_memory_root() -> Path:
    # default: <project>/external_memory
    # allow override if you want later: EXTERNAL_MEMORY=C:\path\to\external_memory
    env = (Path(str(Path().cwd())) if False else None)  # no-op; keeps lint calm
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


@dataclass
class KernelInputs:
    micro: Dict[str, Any]
    macro: Dict[str, Any]
    crash: Dict[str, Any]
    sentiment: Dict[str, Any]


class IntegrativeDecisionKernel:
    """
    Combines tier signals + sentiment into one decision for the UI and execution.

    Writes: external_memory/ai_state/decision_kernel_state.json
    Reads (if present):
      - external_memory/ai_state/tier1_micro_state.json
      - external_memory/ai_state/tier2_macro_state.json
      - external_memory/ai_state/tier3_crash_state.json
      - external_memory/ai_state/sentiment_state.json
    """

    def __init__(self) -> None:
        self.root = _external_memory_root()
        self.ai_state = self.root / "ai_state"
        self.ai_state.mkdir(parents=True, exist_ok=True)

        self.out_path = self.ai_state / "decision_kernel_state.json"

        self.micro_path = self.ai_state / "tier1_micro_state.json"
        self.macro_path = self.ai_state / "tier2_macro_state.json"
        self.crash_path = self.ai_state / "tier3_crash_state.json"
        self.sentiment_path = self.ai_state / "sentiment_state.json"

    def load_inputs(self) -> KernelInputs:
        return KernelInputs(
            micro=_safe_read_json(self.micro_path),
            macro=_safe_read_json(self.macro_path),
            crash=_safe_read_json(self.crash_path),
            sentiment=_safe_read_json(self.sentiment_path),
        )

    def decide(self, inputs: Optional[KernelInputs] = None) -> Dict[str, Any]:
        inputs = inputs or self.load_inputs()

        # Defaults if files don’t exist yet
        micro_signal = str(inputs.micro.get("signal", "hold")).lower()  # buy/sell/hold
        micro_conf = float(inputs.micro.get("confidence", 0.55) or 0.55)

        macro_bias = str(inputs.macro.get("bias", "neutral")).lower()  # bullish/bearish/neutral
        macro_strength = float(inputs.macro.get("strength", 0.5) or 0.5)

        crash_risk = float(inputs.crash.get("crash_risk", inputs.crash.get("risk", 0.0)) or 0.0)  # 0..1
        crash_risk = max(0.0, min(1.0, crash_risk))

        mood = str(inputs.sentiment.get("market_mood", "neutral")).lower()  # bullish/bearish/neutral
        sent_conf = float(inputs.sentiment.get("confidence", 0.55) or 0.55)

        # Hard safety override
        if crash_risk >= 0.80:
            decision = "sell"
            confidence = max(0.75, crash_risk)
            strategy = "crash_override"
        else:
            # Convert macro bias to a directional lean
            macro_dir = 0.0
            if macro_bias in ("bullish", "up", "long"):
                macro_dir = +1.0
            elif macro_bias in ("bearish", "down", "short"):
                macro_dir = -1.0

            # Convert micro signal to direction
            micro_dir = 0.0
            if micro_signal == "buy":
                micro_dir = +1.0
            elif micro_signal == "sell":
                micro_dir = -1.0

            # Convert sentiment to direction
            sent_dir = 0.0
            if mood in ("bullish", "positive", "up"):
                sent_dir = +1.0
            elif mood in ("bearish", "negative", "down"):
                sent_dir = -1.0

            # Weighted vote
            score = (micro_dir * micro_conf * 0.50) + (macro_dir * macro_strength * 0.30) + (sent_dir * sent_conf * 0.20)

            # Apply mild penalty for rising crash risk
            score *= (1.0 - (crash_risk * 0.35))

            if score >= 0.20:
                decision = "buy"
            elif score <= -0.20:
                decision = "sell"
            else:
                decision = "hold"

            confidence = min(0.95, max(0.05, abs(score) + 0.35))
            strategy = "fusion_vote"

        payload = {
            "timestamp": time.time(),
            "decision": decision,
            "confidence": round(float(confidence), 4),
            "strategy": strategy,
            "inputs": {
                "micro": {"signal": micro_signal, "confidence": micro_conf},
                "macro": {"bias": macro_bias, "strength": macro_strength},
                "crash": {"crash_risk": crash_risk},
                "sentiment": {"market_mood": mood, "confidence": sent_conf},
            },
        }

        _safe_write_json(self.out_path, payload)
        return payload
