import datetime
import threading
import time

from backend.core.state import state, sync_with_broker, update_pnl
from backend.live_trader import LiveTrader
from backend.brokers.alpaca_broker import AlpacaBroker
from backend.brokers.config import get_alpaca_config


# =========================================================
# TESTING CONTROL
# =========================================================
ALLOW_AFTER_HOURS_TESTING = True


class TradingController:

    def __init__(self):
        print("[CONTROLLER] Loaded controller v6 (risk-integrated)")

        self.running = False
        self.ai = LiveTrader()

        cfg = get_alpaca_config()
        self.broker = AlpacaBroker(
            api_key=cfg["api_key"],
            secret_key=cfg["secret_key"],
            paper=cfg["paper"],
        )

        self._last_position = "flat"
        self._last_qty = 0
        self._last_entry = None

        # Trade lifecycle
        self._peak_price = None
        self._entry_time = None
        self._scaled_out = False

        # Entry filters
        self._last_price = None
        self._last_trade_time = 0
        self._last_entry_price = None

        self._clear_stale_orders()

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False

    def _run(self):
        while self.running:
            try:
                price = state["price"]

                if price == 0:
                    time.sleep(1)
                    continue

                sync_with_broker(state, self.broker)
                update_pnl(state)

                if not state.get("sync_ok", True):
                    print("[BLOCK] Sync unstable -> trading paused")
                    time.sleep(1)
                    continue

                # 🔥 DEPLOYABLE CAPITAL TRACKING
                state["deployable_capital"] = (
                    state["total_equity"] * state.get("deploy_pct", 0.25)
                )

                self._detect_trade_close(price)

                exit_signal = self._manage_position(price)
                if exit_signal:
                    self._execute(
                        action=exit_signal,
                        price=price,
                        strategy="risk_exit",
                        regime="N/A",
                        confidence=1.0,
                        volatility=0.0,
                    )
                    time.sleep(1)
                    continue

                action, strategy, regime, confidence, volatility = self.ai.decide_action(
                    price,
                    state["equity"],
                )

                print(
                    f"[AI DEBUG] action={action} strategy={strategy} "
                    f"regime={regime} confidence={confidence:.2f} volatility={volatility}"
                )

                self._execute(
                    action=action,
                    price=price,
                    strategy=strategy,
                    regime=regime,
                    confidence=confidence,
                    volatility=volatility,
                )

            except Exception as e:
                state["logs"].append(f"[CTRL ERROR] {e}")

            time.sleep(1)

    def _market_open(self):
        now = datetime.datetime.utcnow()

        if now.weekday() >= 5:
            return False

        open_time = now.replace(hour=13, minute=30, second=0, microsecond=0)
        close_time = now.replace(hour=20, minute=0, second=0, microsecond=0)

        return open_time <= now <= close_time

    # =========================================================
    # POSITION MANAGEMENT
    # =========================================================
    def _manage_position(self, price):
        if state["position"] == "flat":
            return None

        entry = state["entry_price"]
        qty = state["qty"]

        if not entry:
            return None

        pnl_pct = (price - entry) / entry

        if self._peak_price is None:
            self._peak_price = price
        else:
            self._peak_price = max(self._peak_price, price)

        drawdown = (self._peak_price - price) / self._peak_price

        if pnl_pct <= -0.04:
            print(f"[EXIT] STOP_LOSS | pnl={pnl_pct:.4f}")
            return "FULL_EXIT"

        if pnl_pct >= 0.02 and qty >= 2:
            if not self._scaled_out:
                print(f"[EXIT] SCALE OUT | pnl={pnl_pct:.4f}")
                self._scaled_out = True
                return "PARTIAL_EXIT"

        if pnl_pct > 0.02 and drawdown > 0.001:
            print(f"[EXIT] TRAILING STOP | pnl={pnl_pct:.4f} drawdown={drawdown:.4f}")
            return "FULL_EXIT"

        if pnl_pct >= 0.06:
            print(f"[EXIT] MAX PROFIT | pnl={pnl_pct:.4f}")
            return "FULL_EXIT"

        return None

    # =========================================================
    # TRADE CLOSE DETECTION
    # =========================================================
    def _detect_trade_close(self, price):
        current_position = state["position"]

        if self._last_position != "flat" and current_position == "flat":
            pnl = 0.0

            if self._last_entry:
                pnl = (price - self._last_entry) * self._last_qty

            print(f"[TRADE CLOSED] PnL: {pnl:.2f}")

            state["realized_pnl"] += pnl

            state["trades"].append({
                "entry": self._last_entry,
                "exit": price,
                "qty": self._last_qty,
                "pnl": pnl,
                "duration": time.time() - self._entry_time if self._entry_time else 0,
            })

            self._peak_price = None
            self._entry_time = None
            self._scaled_out = False

            state["execution_state"] = "IDLE"
            state["order_pending"] = False
            state["active_order_id"] = None

        self._last_position = current_position
        self._last_qty = state["qty"]
        self._last_entry = state["entry_price"]

    # =========================================================
    # EXECUTION ENGINE
    # =========================================================
    def _execute(self, action, price, strategy, regime, confidence, volatility):
        try:
            now = time.time()

            # 🔴 KILL SWITCH
            if not state.get("trading_enabled", True):
                print("[BLOCK] Trading disabled")
                return

            print(
                f"[EXEC] action={action} price={price} "
                f"position={state['position']} sync_ok={state.get('sync_ok')}"
            )

            market_open = self._market_open()

            if not market_open and not ALLOW_AFTER_HOURS_TESTING:
                print("[BLOCK] Market closed")
                return

            if state["execution_state"] == "PENDING":
                if now - state["last_order_time"] < 15:
                    print("[BLOCK] Order pending")
                    return

                print("[RESET] Pending order timeout -> IDLE")
                state["execution_state"] = "IDLE"
                state["order_pending"] = False
                state["active_order_id"] = None

            if action == "HOLD":
                return

            # =========================
            # SELL / EXIT
            # =========================
            if action in ["SELL", "FULL_EXIT", "PARTIAL_EXIT"]:
                if state["position"] == "flat":
                    return

                pos = self.broker.get_position("SPY")
                if not pos:
                    return

                available_qty = int(float(pos.get("qty_available", 0) or 0))
                if available_qty <= 0:
                    return

                exit_qty = max(1, available_qty // 2) if action == "PARTIAL_EXIT" else available_qty

                if self.broker.place_order("SPY", exit_qty, "sell"):
                    state["execution_state"] = "PENDING"
                    state["last_order_time"] = now
                    state["order_pending"] = True

                return

            # =========================
            # BUY
            # =========================
            if action == "BUY":

                if state["position"] != "flat":
                    return

                if confidence < 0.5:
                    return

                # 🔥 RISK ENGINE
                risk_pct = self.ai.risk.get_risk(
                    action=action,
                    confidence=confidence,
                    equity=state["total_equity"],
                    volatility=volatility,
                    strategy=strategy,
                    regime=regime,
                    performance={"margin_pressure": state.get("margin_pressure", 0)},
                    deploy_pct=state.get("deploy_pct", 0.25),
                )

                # 🔒 UI CAP
                risk_pct = min(risk_pct, state.get("risk_per_trade", 0.01))

                position_value = state["total_equity"] * risk_pct
                qty = max(1, int(position_value // price))

                # 🚨 EXPOSURE GUARD
                max_allowed = state["total_equity"] * state["max_exposure_pct"]

                if qty * price > max_allowed:
                    print("[BLOCK] Exposure limit hit")
                    return

                print(f"[BUY] qty={qty} risk={risk_pct:.4f}")

                if self.broker.place_order("SPY", qty, "buy"):
                    state["execution_state"] = "PENDING"
                    state["last_order_time"] = now
                    state["order_pending"] = True

        except Exception as e:
            state["logs"].append(f"[EXEC ERROR] {e}")

    def _clear_stale_orders(self):
        try:
            orders = self.broker.list_orders()
            for o in orders:
                self.broker.cancel_order(o["id"])
        except Exception:
            pass