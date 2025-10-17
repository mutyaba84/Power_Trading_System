from pathlib import Path
import numpy as np
import json

class StrategyEmbeddings:
    def __init__(self, base_path="/app/external_memory/memory/embeddings"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def embed_episode(self, episode):
        # Dummy embedding: for real-world, replace with neural embedding
        vector = np.array([sum([trade["pnl"] for trade in episode])/len(episode)])
        return vector

    def save_embedding(self, episode_id, vector):
        file = self.base / f"{episode_id}.json"
        file.write_text(json.dumps(vector.tolist()))
        return file

    def load_embeddings(self):
        vectors = []
        for f in self.base.glob("*.json"):
            vectors.append(np.array(json.loads(f.read_text())))
        return vectors
