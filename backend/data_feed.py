import pandas as pd, time, random
from pathlib import Path

class DataFeed:
    def __init__(self, source="/app/external_memory/data/historical.csv"):
        self.source = Path(source)
        if self.source.exists():
            self.df = pd.read_csv(self.source)
        else:
            self.df = pd.DataFrame({
                "timestamp": pd.date_range("2024-01-01", periods=1000, freq="H"),
                "price": [100 + random.uniform(-1,1) for _ in range(1000)]
            })
        self.idx = 0

    def next_tick(self):
        if self.idx >= len(self.df): self.idx = 0
        row = self.df.iloc[self.idx]
        self.idx += 1
        time.sleep(0.1)
        return dict(timestamp=row["timestamp"], price=row["price"])
