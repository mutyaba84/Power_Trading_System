import json
import os
import time
import random

AI_STATE_DIR = os.getenv("AI_STORAGE_PATH", "external_memory/ai_state")
os.makedirs(AI_STATE_DIR, exist_ok=True)

def run_dummy_feed():
    print("[AI] Dummy market feed started")

    while True:
        sentiment = {
            "timestamp": time.time(),
            "market_mood": random.choice(["bullish", "bearish", "neutral"]),
            "confidence": round(random.uniform(0.55, 0.95), 2),
            "volatility": round(random.uniform(0.1, 0.8), 2),
            "source": "dummy_market_feed"
        }

        with open(os.path.join(AI_STATE_DIR, "sentiment_state.json"), "w") as f:
            json.dump(sentiment, f)

        print("[AI] Sentiment updated →", sentiment)
        time.sleep(5)
