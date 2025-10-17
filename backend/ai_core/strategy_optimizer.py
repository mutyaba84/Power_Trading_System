from .episodic_memory import EpisodicMemory
from .strategy_embeddings import StrategyEmbeddings
import numpy as np
import json, time
from pathlib import Path

class StrategyOptimizer:
    def __init__(self, external_memory="/app/external_memory/memory"):
        self.memory_path = Path(external_memory)
        self.episodic = EpisodicMemory(self.memory_path / "episodes")
        self.embeddings = StrategyEmbeddings(self.memory_path / "embeddings")
        self.optimized_dir = self.memory_path / "knowledge_graphs"
        self.optimized_dir.mkdir(parents=True, exist_ok=True)

    def optimize(self):
        # Load last 50 episodes
        episodes = self.episodic.load_recent(50)
        if not episodes: return {"status": "no_data"}

        # Aggregate PnL vectors
        vectors = [self.embeddings.embed_episode(ep) for ep in episodes]
        mean_vector = np.mean(vectors, axis=0)

        # Generate a simple “strategy rule” based on historical trends
        strategy = {
            "recommended_action": "buy" if mean_vector[0] > 0 else "sell",
            "expected_avg_pnl": float(mean_vector[0]),
            "timestamp": time.time()
        }

        # Save to knowledge graph
        filename = self.optimized_dir / f"strategy_{int(time.time())}.json"
        filename.write_text(json.dumps(strategy, indent=2))
        return strategy
