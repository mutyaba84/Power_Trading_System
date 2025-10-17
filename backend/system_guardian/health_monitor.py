import psutil, shutil, time
from ai_core.memory_manager import MemoryManager

class HealthMonitor:
    def __init__(self):
        self.memory = MemoryManager()

    def check_system(self):
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(self.memory.base).percent
        self.memory.log_event(f"System Health | CPU:{cpu}% RAM:{ram}% Disk:{disk}%")
        alerts = []
        if cpu > 90: alerts.append("CPU overload")
        if ram > 90: alerts.append("RAM critical")
        if disk > 95: alerts.append("Disk almost full")
        return alerts
