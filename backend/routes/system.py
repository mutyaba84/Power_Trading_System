import os
import time
import platform
import subprocess
from fastapi import APIRouter

from backend.utils.event_log import log_event

# FIX: add router prefix
router = APIRouter(prefix="/system", tags=["system"])


def _get_free_memory_gb() -> float | None:
    """
    Best-effort free memory in GB.
    - On Windows: uses CIM via PowerShell
    - On non-Windows: returns None
    """
    try:
        if platform.system().lower() != "windows":
            return None

        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory",
        ]

        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()

        free_kb = float(out)

        return round(free_kb / (1024 * 1024), 2)

    except Exception:
        return None


@router.get("/status")
def system_status():

    equity = float(os.getenv("PAPER_EQUITY", "10000.0"))
    risk_limit = float(os.getenv("RISK_LIMIT", "0.02"))

    payload = {
        "status": "ONLINE",
        "engine": "live",
        "mode": "simulation",
        "timestamp": time.time(),
        "free_memory_gb": _get_free_memory_gb(),
        "equity": equity,
        "risk_limit": risk_limit,
    }

    # Avoid log spam (dashboard polls frequently)
    # log_event("system.status", **payload)

    return payload


@router.get("/info")
def info():
    """
    Developer-friendly system information.
    """
    return {
        "app": "Power Trading System",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "time": time.time(),
    }