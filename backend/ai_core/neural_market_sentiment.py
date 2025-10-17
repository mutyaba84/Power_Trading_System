"""
Neural Market Sentiment Interface
---------------------------------
Reads textual market data, converts it into sentiment vectors, and
writes rolling sentiment indexes into external memory for other
AI modules to use.

Runs in simulation / research mode only.
"""

import json
import random
from datetime import datetime
from pathlib import Path
import numpy as np

# External persistent storage
EXTERNAL_MEMORY = Path("/app/external_memory")
SENTIMENT_CACHE = EXTERNAL_MEMORY / "sentiment_cache"
LOG_FILE = EXTERNAL_MEMORY / "logs" / "sentiment.log"

SENTIMENT_CACHE.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class NeuralMarketSentiment:
    def __init__(self):
        self.sentiment_history = []
        self.max_history = 500  # configurable rolling window
        self.log("Sentiment engine initialized.")

    def log(self, msg: str):
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

    def _mock_text_feed(self):
        """Synthetic text feed placeholder."""
        samples = [
            "Markets show strong growth potential.",
            "Investors fear upcoming inflation reports.",
            "Tech stocks rally as AI adoption expands.",
            "Recession concerns weigh on consumer sentiment.",
        ]
        return random.choice(samples)

    def _analyze_text(self, text: str):
        """Very simple placeholder sentiment model."""
        pos_words = ["strong", "growth", "rally", "expands", "optimism"]
        neg_words = ["fear", "recession", "concerns", "inflation", "weigh"]
        score = sum(w in text.lower() for w in pos_words) - sum(
            w in text.lower() for w in neg_words
        )
        return max(-1.0, min(1.0, score / 3))

    def update(self, text: str = None):
        """Feed new text or generate synthetic one."""
        text = text or self._mock_text_feed()
        score = self._analyze_text(text)
        self.sentiment_history.append(score)
        if len(self.sentiment_history) > self.max_history:
            self.sentiment_history.pop(0)
        self.log(f"Processed text: '{text}' | score={score:+.2f}")
        self._save_state()
        return score

    def _save_state(self):
        """Persist rolling sentiment history to external memory."""
        cache_path = SENTIMENT_CACHE / "sentiment_state.json"
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(self.sentiment_history, f)

    def get_index(self):
        """Return a smoothed sentiment index (-1 bearish, +1 bullish)."""
        if not self.sentiment_history:
            return 0.0
        arr = np.array(self.sentiment_history)
        return float(np.tanh(arr.mean()))

    def summary(self):
        index = self.get_index()
        self.log(f"Sentiment index computed: {index:+.2f}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment_index": index,
            "samples": len(self.sentiment_history),
        }


if __name__ == "__main__":
    engine = NeuralMarketSentiment()
    for _ in range(10):  # simulate feed updates
        engine.update()
    print(engine.summary())
