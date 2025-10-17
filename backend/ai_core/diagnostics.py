from .memory_manager import MemoryManager
import os, psutil

def run_diagnostics():
    mem = MemoryManager()
    info = {
        "free_space_gb": psutil.disk_usage(mem.base).free / (1024**3),
        "folders": {k: str(v) for k, v in mem.paths.items()},
        "cpu_usage": psutil.cpu_percent(interval=1),
        "ram_usage": psutil.virtual_memory().percent
    }
    mem.save_json("system_diagnostics", info)
    mem.log_event("Diagnostics completed successfully.")
    return info
