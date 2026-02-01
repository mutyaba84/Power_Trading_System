from backend.storage.sqlite_adapter import SQLiteStorage

storage = SQLiteStorage(
    db_path="/var/lib/trading/trading_state.db"
)
