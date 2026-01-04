# backend/app/ai_core/utils/persistence.py
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional


def ai_core_read_only() -> bool:
    v = os.getenv("AI_CORE_READ_ONLY", "true").strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _acquire_lock(lock_path: Path, *, timeout_sec: float = 2.0, stale_sec: float = 20.0) -> bool:
    """
    Cross-process lock via O_EXCL lock file.
    - timeout: how long we wait to acquire
    - stale: if lock file is older than stale_sec, we consider it stale and remove it
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()

    while True:
        try:
            # stale lock cleanup
            if lock_path.exists():
                try:
                    age = time.time() - lock_path.stat().st_mtime
                    if age > stale_sec:
                        try:
                            lock_path.unlink()
                        except Exception:
                            pass
                except Exception:
                    pass

            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            if (time.time() - start) >= timeout_sec:
                return False
            time.sleep(0.02)


def _release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except Exception:
        pass


def atomic_write_json(
    path: str | Path,
    data: Dict[str, Any],
    *,
    indent: Optional[int] = None,
    retries: int = 12,
    backoff_base: float = 0.015,
    lock_timeout_sec: float = 2.0,
) -> bool:
    """
    Atomic write with:
    - cross-process lock
    - retry/backoff for Windows rename collisions
    Returns True if wrote successfully, False if skipped/failed.

    IMPORTANT: Will skip writing if AI_CORE_READ_ONLY=true.
    """
    if ai_core_read_only():
        return False

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lock_path = p.with_suffix(p.suffix + ".lock")
    got_lock = _acquire_lock(lock_path, timeout_sec=lock_timeout_sec)
    if not got_lock:
        # Another process is writing; skip quietly.
        return False

    tmppath = None
    try:
        # Unique temp file in same directory (needed for atomic replace)
        fd, tmppath = tempfile.mkstemp(prefix=p.name + ".tmp.", suffix=".json", dir=str(p.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            try:
                os.close(fd)
            except Exception:
                pass
            raise

        # Windows-safe replace with retries
        for i in range(max(1, retries)):
            try:
                os.replace(tmppath, str(p))
                tmppath = None
                return True
            except PermissionError:
                # target likely open by another process; backoff
                time.sleep(backoff_base * (2 ** min(i, 6)))
            except OSError:
                time.sleep(backoff_base * (2 ** min(i, 6)))

        return False
    finally:
        _release_lock(lock_path)
        if tmppath:
            try:
                os.remove(tmppath)
            except Exception:
                pass


def append_jsonl(path: str | Path, record: Dict[str, Any]) -> bool:
    """
    Append-only JSONL. Much less likely to hit rename issues.
    Skips writing in read-only mode.
    """
    if ai_core_read_only():
        return False

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = dict(record)
    rec.setdefault("ts", time.time())
    line = json.dumps(rec, ensure_ascii=False)

    # lock to avoid interleaved writes across processes
    lock_path = p.with_suffix(p.suffix + ".lock")
    got_lock = _acquire_lock(lock_path, timeout_sec=2.0)
    if not got_lock:
        return False

    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        return True
    finally:
        _release_lock(lock_path)
