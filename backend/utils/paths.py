from __future__ import annotations

import os
from pathlib import Path

def project_root() -> Path:
    # backend/utils/paths.py -> backend -> project root
    return Path(__file__).resolve().parents[2]

def storage_root() -> Path:
    """
    Safe storage directory.
    Priority:
      1) AI_STORAGE_PATH (if it can be created/used)
      2) <project_root>/external_memory
    """
    default_root = project_root() / "external_memory"
    raw = os.getenv("AI_STORAGE_PATH")

    if not raw:
        default_root.mkdir(parents=True, exist_ok=True)
        return default_root

    p = Path(raw)
    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        default_root.mkdir(parents=True, exist_ok=True)
        return default_root

def ai_state_dir() -> Path:
    d = storage_root() / "ai_state"
    d.mkdir(parents=True, exist_ok=True)
    return d

def logs_dir() -> Path:
    d = storage_root() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d

def kill_switch_path() -> Path:
    return storage_root() / "KILL_SWITCH"
