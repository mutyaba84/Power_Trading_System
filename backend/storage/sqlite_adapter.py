import sqlite3
from pathlib import Path
from typing import Optional, List
from backend.storage.base import Storage


class SQLiteStorage(Storage):
    def __init__(self, db_path: str):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def log_trade(
        self,
        *,
        timestamp: float,
        symbol: str,
        side: str,
        size: float,
        price: float,
        strategy: str,
        confidence: float,
        pnl: Optional[float],
        simulated: bool,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO trades
            (timestamp, symbol, side, size, price, strategy, confidence, pnl, simulated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                symbol,
                side,
                size,
                price,
                strategy,
                confidence,
                pnl,
                int(simulated),
            ),
        )
        self.conn.commit()

    def record_equity(self, timestamp: float, equity: float) -> None:
        self.conn.execute(
            """
            INSERT INTO equity_snapshots (timestamp, equity)
            VALUES (?, ?)
            """,
            (timestamp, equity),
        )
        self.conn.commit()

    def get_equity_since(self, since_ts: float) -> List[float]:
        cur = self.conn.execute(
            """
            SELECT equity FROM equity_snapshots
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (since_ts,),
        )
        return [r["equity"] for r in cur.fetchall()]
