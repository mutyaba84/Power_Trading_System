from pathlib import Path
import json, time

class EpisodicMemory:
    def __init__(self, base_path="/app/external_memory/memory/episodes"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def store_episode(self, episode_id, data):
        file = self.base / f"{episode_id}_{int(time.time())}.json"
        file.write_text(json.dumps(data, indent=2))
        return file

    def load_recent(self, n=10):
        files = sorted(self.base.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        episodes = []
        for f in files[:n]:
            episodes.append(json.loads(f.read_text()))
        return episodes
