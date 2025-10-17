import torch
from pathlib import Path

class ModelCheckpoint:
    def __init__(self, dir_path="/app/external_memory/models"):
        self.dir = Path(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, model, name):
        torch.save(model.state_dict(), self.dir / f"{name}.pt")

    def load(self, model, name):
        path = self.dir / f"{name}.pt"
        if path.exists():
            model.load_state_dict(torch.load(path, map_location="cpu"))
        return model
