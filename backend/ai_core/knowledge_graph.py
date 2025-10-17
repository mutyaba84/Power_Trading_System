import networkx as nx
from pathlib import Path
import pickle

class KnowledgeGraph:
    def __init__(self, path: str = "/app/external_memory/knowledge/graph.pkl"):
        self.path = Path(path)
        self.graph = nx.DiGraph()
        if self.path.exists():
            with open(self.path, "rb") as f:
                self.graph = pickle.load(f)

    def add_experience(self, event, outcome, context=None):
        self.graph.add_node(event, outcome=outcome, context=context)
        if context:
            for c in context:
                self.graph.add_edge(c, event)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "wb") as f:
            pickle.dump(self.graph, f)
