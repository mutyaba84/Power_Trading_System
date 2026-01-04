# backend/app/ai_core/runtime_mode.py
from __future__ import annotations
import os

def ai_core_read_only() -> bool:
    """
    If TRUE, AI core must not write any persistent state.
    Default True when running API/server.
    """
    v = os.getenv("AI_CORE_READ_ONLY", "true").strip().lower()
    return v in ("1", "true", "yes", "y", "on")
