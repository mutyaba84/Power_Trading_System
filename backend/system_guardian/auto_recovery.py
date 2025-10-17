from ai_core.memory_manager import MemoryManager

class AutoRecovery:
    def __init__(self):
        self.memory = MemoryManager()

    def recover(self, alerts, broker_status):
        actions = []
        if alerts:
            actions.append("Pausing trading due to system alerts")
        if any(status=="FAIL" for status in broker_status.values()):
            actions.append("Restarting affected broker connections")
        for act in actions:
            self.memory.log_event(f"AutoRecovery action: {act}")
        return actions
