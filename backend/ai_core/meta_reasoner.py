from .episodic_memory import EpisodicMemory
from .strategy_embeddings import StrategyEmbeddings
import numpy as np

class MetaReasoner:
    def __init__(self):
        self.memory = EpisodicMemory()
        self.embeddings = StrategyEmbeddings()

    def analyze(self):
        episodes = self.memory.load_recent(20)
        vectors = [self.embeddings.embed_episode(ep) for ep in episodes]
        if not vectors: return {"insight": "No data"}
        mean_vector = np.mean(vectors, axis=0)
        return {"insight": f"Avg pnl over last 20 episodes: {mean_vector[0]:.2f}"}
