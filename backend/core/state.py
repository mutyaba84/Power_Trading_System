import time

state = {
    "price": 0.0,

    "position": "flat",
    "qty": 0,
    "entry_price": None,

    "equity": 0.0,
    "total_equity": 0.0,
    "cash": 0.0,
    "buying_power": 0.0,
    "can_trade": False,

    "realized_pnl": 0.0,
    "unrealized_pnl": 0.0,

    "trades": [],
    "logs": [],
    "last_action": "HOLD",

    "margin_pressure": 0.0,

    # legacy flags
    "order_pending": False,
    "order_timestamp": 0,

    # execution engine
    "execution_state": "IDLE",   # IDLE / PENDING / COOLDOWN
    "last_order_time": 0,
    "last_order_side": None,
    "active_order_id": None,

    # portfolio controls
    "max_exposure_pct": 0.25,
    "deploy_pct": 0.25,
}


def sync_with_broker(state, broker):
    try:
        account = broker.get_account()
        pos = broker.get_position("SPY")

        cash = float(account.cash)
        total_equity = float(account.equity)
        broker_buying_power = float(account.buying_power)

        deploy_pct = state.get("deploy_pct", 0.25)
        deployable_equity = total_equity * deploy_pct

        state["cash"] = cash
        state["total_equity"] = total_equity
        state["equity"] = deployable_equity

        # margin pressure
        if cash < 0:
            state["margin_pressure"] = min(1.0, abs(cash) / max(total_equity, 1e-9))
        else:
            state["margin_pressure"] = 0.0

        # position sync
        if pos and float(pos.get("qty", 0)) != 0:
            qty = float(pos.get("qty", 0))
            state["position"] = "long" if qty > 0 else "short"
            state["qty"] = abs(int(qty))
            state["entry_price"] = float(pos.get("avg_price", 0.0) or 0.0)

            # hard capital lock while in a position
            state["buying_power"] = 0.0
            state["can_trade"] = False

            # if broker confirms position, clear pending state
            if state["execution_state"] == "PENDING":
                state["execution_state"] = "IDLE"
                state["active_order_id"] = None
                state["order_pending"] = False

        else:
            state["position"] = "flat"
            state["qty"] = 0
            state["entry_price"] = None

            state["buying_power"] = min(broker_buying_power, deployable_equity)
            state["can_trade"] = state["execution_state"] == "IDLE" and state["buying_power"] > 0

        # fail-safe timeout for stuck pending state
        if state["execution_state"] == "PENDING":
            if time.time() - state["last_order_time"] > 20:
                state["execution_state"] = "COOLDOWN"
                state["last_order_time"] = time.time()
                state["active_order_id"] = None
                state["order_pending"] = False
                state["logs"].append("[SYNC] Pending order timeout -> COOLDOWN")

    except Exception as e:
        state["logs"].append(f"[SYNC ERROR] {e}")


def update_pnl(state):
    price = state["price"]

    if state["position"] == "long" and state["entry_price"]:
        state["unrealized_pnl"] = (price - state["entry_price"]) * state["qty"]
    elif state["position"] == "short" and state["entry_price"]:
        state["unrealized_pnl"] = (state["entry_price"] - price) * state["qty"]
    else:
        state["unrealized_pnl"] = 0.0