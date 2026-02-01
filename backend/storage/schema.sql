-- ============================
-- Trades (immutable record)
-- ============================
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,               -- BUY / SELL
    size REAL NOT NULL,
    price REAL NOT NULL,
    strategy TEXT NOT NULL,
    confidence REAL NOT NULL,
    pnl REAL,
    simulated INTEGER NOT NULL        -- 1 = sim, 0 = live
);

-- ============================
-- Positions (current state)
-- ============================
CREATE TABLE IF NOT EXISTS positions (
    symbol TEXT PRIMARY KEY,
    size REAL NOT NULL,
    avg_price REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- ============================
-- Equity snapshots
-- ============================
CREATE TABLE IF NOT EXISTS equity_snapshots (
    timestamp REAL PRIMARY KEY,
    equity REAL NOT NULL
);

-- ============================
-- Model feedback / learning memory
-- ============================
CREATE TABLE IF NOT EXISTS model_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    strategy TEXT NOT NULL,
    confidence REAL NOT NULL,
    outcome REAL NOT NULL             -- normalized reward / pnl
);
