import time

# =========================================================
# GLOBAL STATE
# =========================================================

state = {
    "price": 0.0,

    # position
    "position": "flat",
    "qty": 0,
    "entry_price": None,

    # account
    "equity": 0.0,
    "total_equity": 0.0,
    "cash": 0.0,
    "buying_power": 0.0,
    "can_trade": False,

    # pnl
    "realized_pnl": 0.0,
    "unrealized_pnl": 0.0,

    # history / diagnostics
    "trades": [],
    "logs": [],
    "last_action": "HOLD",

    # risk
    "margin_pressure": 0.0,

    # order execution
    "order_pending": False,
    "order_timestamp": 0,
    "execution_state": "IDLE",  # IDLE/PENDING/COOLDOWN
    "last_order_time": 0,
    "last_order_side": None,
    "active_order_id": None,

    # portfolio controls
    "max_exposure_pct": 0.25,
    "deploy_pct": 0.25,

    # sync health
    "sync_ok": True,
}


# =========================================================
# LOGGING HELPER
# =========================================================

def _log_once(message: str):
    if not state["logs"] or state["logs"][-1] != message:
        state["logs"].append(message)


# =========================================================
# BROKER SYNC
# =========================================================

def sync_with_broker(state, broker):
    try:
        # assume healthy unless proven otherwise
        state["sync_ok"] = True

        # ---------------------------------------------------
        # ACCOUNT FETCH
        # ---------------------------------------------------
        account = broker.get_account()

        if not account:
            _log_once("[SYNC WARNING] account returned None")
            state["sync_ok"] = False
            return

        cash = getattr(account, "cash", None)
        equity = getattr(account, "equity", None)
        buying_power = getattr(account, "buying_power", None)

        if cash is None or equity is None or buying_power is None:
            _log_once("[SYNC WARNING] missing account fields")
            state["sync_ok"] = False
            return

        cash = float(cash)
        total_equity = float(equity)
        broker_buying_power = float(buying_power)

        # ---------------------------------------------------
        # DEPLOYMENT CONTROL
        # ---------------------------------------------------
        deploy_pct = state.get("deploy_pct", 0.25)
        deployable_equity = total_equity * deploy_pct

        state["cash"] = cash
        state["total_equity"] = total_equity
        state["equity"] = deployable_equity

        # ---------------------------------------------------
        # MARGIN PRESSURE
        # ---------------------------------------------------
        if cash < 0:
            state["margin_pressure"] = min(
                1.0,
                abs(cash) / max(total_equity, 1e-9)
            )
        else:
            state["margin_pressure"] = 0.0

        # ---------------------------------------------------
        # POSITION SYNC
        # ---------------------------------------------------
        try:
            pos = broker.get_position("SPY")
        except Exception:
            pos = None

        if pos and pos.get("qty") is not None and float(pos.get("qty", 0)) != 0:

            qty = float(pos["qty"])

            state["position"] = "long" if qty > 0 else "short"
            state["qty"] = abs(int(qty))
            state["entry_price"] = float(
                pos.get("avg_price", 0.0) or 0.0
            )

            # lock capital while in trade
            state["buying_power"] = 0.0
            state["can_trade"] = False

            # clear pending if broker confirms filled position
            if state["execution_state"] == "PENDING":
                state["execution_state"] = "IDLE"
                state["active_order_id"] = None
                state["order_pending"] = False

        else:
            state["position"] = "flat"
            state["qty"] = 0
            state["entry_price"] = None

            state["buying_power"] = min(
                broker_buying_power,
                deployable_equity
            )

            state["can_trade"] = (
                state["execution_state"] == "IDLE"
                and state["buying_power"] > 0
            )

        # ---------------------------------------------------
        # STUCK ORDER FAILSAFE
        # ---------------------------------------------------
        if state["execution_state"] == "PENDING":

            age = time.time() - state["last_order_time"]

            if age > 45:
                _log_once(
                    "[SYNC WARNING] pending order taking long"
                )

                try:
                    pos = broker.get_position("SPY")
                except Exception:
                    pos = None

                if pos and float(pos.get("qty", 0)) != 0:
                    # probably filled, release pending
                    state["execution_state"] = "IDLE"
                    state["active_order_id"] = None
                    state["order_pending"] = False
                    state["sync_ok"] = True

                else:
                    # unresolved order -> cooldown
                    state["execution_state"] = "COOLDOWN"
                    state["last_order_time"] = time.time()
                    state["active_order_id"] = None
                    state["order_pending"] = False

                    _log_once(
                        "[SYNC] forced cooldown after failed verification"
                    )

        # successful sync
        state["sync_ok"] = True

    except Exception as e:
        _log_once(f"[SYNC ERROR] {e}")
        state["sync_ok"] = False


# =========================================================
# PNL UPDATE
# =========================================================

def update_pnl(state):
    price = state["price"]

    if (
        state["position"] == "long"
        and state["entry_price"]
    ):
        state["unrealized_pnl"] = (
            price - state["entry_price"]
        ) * state["qty"]

    elif (
        state["position"] == "short"
        and state["entry_price"]
    ):
        state["unrealized_pnl"] = (
            state["entry_price"] - price
        ) * state["qty"]

    else:
        state["unrealized_pnl"] = 0.0