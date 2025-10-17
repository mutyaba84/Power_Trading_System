from .memory_manager import MemoryManager
from .knowledge_graph import KnowledgeGraph
import random

class LearningEngine:
    def __init__(self):
        self.memory = MemoryManager()
        self.graph = KnowledgeGraph()

    def reinforce(self, event, reward, context=None):
        # Update long-term memory
        self.graph.add_experience(event, reward, context)
        self.graph.save()
        # Log the reward signal
        self.memory.log_event(f"Reinforced {event} with reward {reward}")

    def recall_best_actions(self, context):
        # Simple heuristic for now
        nodes = [n for n, d in self.graph.graph.nodes(data=True)
                 if d.get("context") == context]
        if not nodes:
            return []
        nodes.sort(key=lambda n: self.graph.graph.nodes[n]["outcome"], reverse=True)
        return nodes[:3]
