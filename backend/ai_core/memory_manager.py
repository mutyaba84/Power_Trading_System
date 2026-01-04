from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from backend.utils.logger import get_logger
from backend.utils.paths import storage_root

logger = get_logger("MemoryManager")

# Option 2 import path
try:
    from backend.utils.persistence import append_jsonl, atomic_write_json, ai_core_read_only  # type: ignore
except Exception:
    append_jsonl = None  # type: ignore
    atomic_write_json = None  # type: ignore

    def ai_core_read_only() -> bool:
        v = os.getenv("AI_CORE_READ_ONLY", "true").strip().lower()
        return v in ("1", "true", "yes", "y", "on")


class MemoryManager:
    """
    Runtime-safe external memory helper.

    RULES:
    - JSON only
    - Append-only logs for runtime
    - No pickle
    - Overwrites only via atomic_write_json
    - Respects AI_CORE_READ_ONLY
    """

    def __init__(self, base_path: Optional[str] = None) -> None:
        self.base = Path(base_path) if base_path else storage_root()

        self.paths = {
            "logs": self.base / "logs",
            "ai_state": self.base / "ai_state",
            "ai_core": self.base / "ai_core",
        }

        for p in self.paths.values():
            p.mkdir(parents=True, exist_ok=True)

        logger.info("MemoryManager initialized (runtime-safe).")

    def save_json(self, rel_dir: str, name: str, data: Any) -> Optional[Path]:
        if ai_core_read_only():
            return None

        target_dir = self.paths.get(rel_dir, self.base / rel_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        path = target_dir / f"{name}.json"
        try:
            if atomic_write_json is not None:
                atomic_write_json(path, data, indent=2)  # type: ignore
            else:
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return path
        except Exception as e:
            logger.warning(f"save_json failed (ok): {e}")
            return None

    def load_json(self, rel_dir: str, name: str, default: Any = None) -> Any:
        target_dir = self.paths.get(rel_dir, self.base / rel_dir)
        path = target_dir / f"{name}.json"
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def append(self, record: Any) -> None:
        if ai_core_read_only():
            return
        try:
            if append_jsonl is not None:
                append_jsonl(self.paths["ai_core"] / "events.jsonl", record)  # type: ignore
            else:
                p = self.paths["ai_core"] / "events.jsonl"
                with p.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"ts": time.time(), "record": record}, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Memory append failed (ok): {e}")

    def log_event(self, msg: str) -> None:
        if ai_core_read_only():
            return
        try:
            rec = {"msg": msg, "ts": time.time()}
            p = self.paths["logs"] / f"session_{time.strftime('%Y%m%d')}.jsonl"
            if append_jsonl is not None:
                append_jsonl(p, rec)  # type: ignore
            else:
                with p.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write memory log (ok): {e}")
