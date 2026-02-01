import sqlite3
import time
from pathlib import Path
from typing import Optional

DB_PATH = Path("backend/data/trading_state.db")


class Persistence:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    # -------------------------
    # TRADE LOGGING
    # -------------------------
    def log_trade(
        self,
        *,
        symbol: str,
        side: str,
        size: float,
        price: float,
        strategy: str,
        confidence: float,
        pnl: Optional[float],
        simulated: bool,
    ):
        self.conn.execute(
            """
            INSERT INTO trades
            (timestamp, symbol, side, size, price, strategy, confidence, pnl, simulated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                time.time(),
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

    # -------------------------
    # EQUITY SNAPSHOT
    # -------------------------
    def record_equity(self, equity: float):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO equity_snapshots
            (timestamp, equity)
            VALUES (?, ?)
            """,
            (time.time(), equity),
        )
        self.conn.commit()

    # -------------------------
    # DAILY DRAWDOWN QUERY
    # -------------------------
    def get_equity_since(self, since_ts: float):
        cur = self.conn.execute(
            """
            SELECT equity FROM equity_snapshots
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (since_ts,),
        )
        rows = cur.fetchall()
        return [r["equity"] for r in rows]
