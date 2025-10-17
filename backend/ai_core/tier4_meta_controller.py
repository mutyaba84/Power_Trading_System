"""
Tier 4 – Meta Controller: orchestrates sub-AIs, chooses best strategy.
"""
from ai_core.tier1_micro_prediction import micro_ai
from utils.logger import get_logger
logger = get_logger("meta_controller")

class MetaController:
    def __init__(self):
        self.mode = "simulation"

    def decide(self, data):
        signal = micro_ai.predict(data)
        logger.info(f"MetaController selected action: {signal}")
        return signal

meta_controller = MetaController()
