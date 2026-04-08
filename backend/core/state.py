state = {
    # -------------------------
    # MARKET
    # -------------------------
    "price": 0.0,

    # -------------------------
    # POSITION
    # -------------------------
    "position": "flat",
    "qty": 0,
    "entry_price": None,

    # -------------------------
    # ACCOUNT
    # -------------------------
    "equity": 0.0,
    "cash": 0.0,
    "buying_power": 0.0,
    "can_trade": False,

    # -------------------------
    # PERFORMANCE
    # -------------------------
    "realized_pnl": 0.0,
    "unrealized_pnl": 0.0,
    "trade_count": 0,
    "win_count": 0,
    "loss_count": 0,

    # -------------------------
    # TRADE HISTORY
    # -------------------------
    "trades": [],

    # -------------------------
    # LOGGING
    # -------------------------
    "logs": [],
    "last_action": "HOLD",
}