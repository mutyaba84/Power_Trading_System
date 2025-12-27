import json
import os

AI_STATE_DIR = os.getenv(
    "AI_STORAGE_PATH",
    "D:/AI_Trading_Storage/ai_state"
)

def read_json(filename):
    try:
        full_path = os.path.join(AI_STATE_DIR, filename)
        with open(full_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

def get_latest_decision():
    return read_json("decision_kernel_state.json")

def get_paper_trading_state():
    return read_json("paper_trading_state.json")
