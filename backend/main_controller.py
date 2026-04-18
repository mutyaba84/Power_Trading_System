import datetime
import threading
import time

from backend.core.state import state, sync_with_broker, update_pnl
from backend.live_trader import LiveTrader
from backend.brokers.alpaca_broker import AlpacaBroker
from backend.brokers.config import get_alpaca_config


class TradingController:

    def __init__(self):
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

        self._position_lock = False
        self._position_lock_time = 0.0

        # 🔥 NEW: trade lifecycle tracking
        self._peak_price = None
        self._entry_time = None

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

                # 🔥 Detect closed trades
                self._detect_trade_close(price)

                # 🔥 Smart exit management BEFORE AI
                exit_signal = self._manage_position(price)
                if exit_signal:
                    print(f"[EXIT] {exit_signal}")
                    self._execute(
                        action="SELL",
                        price=price,
                        strategy="risk_exit",
                        regime="N/A",
                        confidence=1.0,
                        volatility=0.0,
                    )
                    time.sleep(1)
                    continue

                # Stability guard
                recent_logs = "".join(state["logs"][-3:])
                if "[SYNC ERROR]" in recent_logs:
                    print("[BLOCK] Sync unstable -> trading paused")
                    time.sleep(2)
                    continue

                # AI decision
                action, strategy, regime, confidence, volatility = self.ai.decide_action(
                    price,
                    state["equity"],
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

    def _market_open(self) -> bool:
        now = datetime.datetime.utcnow()

        if now.weekday() >= 5:
            return False

        open_time = now.replace(hour=13, minute=30, second=0, microsecond=0)
        close_time = now.replace(hour=20, minute=0, second=0, microsecond=0)

        return open_time <= now <= close_time

    # =========================================================
    # 🔥 POSITION MANAGEMENT (NEW)
    # =========================================================
    def _manage_position(self, price: float):
        if state["position"] == "flat":
            return None

        entry = state["entry_price"]
        pnl_pct = (price - entry) / entry

        # Track peak (for trailing stop)
        if self._peak_price is None:
            self._peak_price = price
        else:
            self._peak_price = max(self._peak_price, price)

        drawdown = (self._peak_price - price) / self._peak_price

        # Stop loss
        if pnl_pct <= -0.01:
            return "STOP_LOSS"

        # Take profit
        if pnl_pct >= 0.02:
            return "TAKE_PROFIT"

        # Trailing stop
        if pnl_pct > 0.01 and drawdown > 0.005:
            return "TRAILING_STOP"

        return None

    # =========================================================
    # 🔥 TRADE CLOSE DETECTION (UPGRADED)
    # =========================================================
    def _detect_trade_close(self, price: float):
        current_position = state["position"]

        if self._last_position != "flat" and current_position == "flat":
            pnl = 0.0

            if self._last_position == "long" and self._last_entry is not None:
                pnl = (price - self._last_entry) * self._last_qty
            elif self._last_position == "short" and self._last_entry is not None:
                pnl = (self._last_entry - price) * self._last_qty

            print(f"[TRADE CLOSED] PnL: {pnl:.2f}")

            # ✅ Realized PnL
            state["realized_pnl"] += pnl

            # ✅ Trade log
            state["trades"].append({
                "entry": self._last_entry,
                "exit": price,
                "qty": self._last_qty,
                "pnl": pnl,
                "duration": time.time() - self._entry_time if self._entry_time else None
            })

            # AI updates
            self.ai.performance.record(
                strategy="mean_reversion",
                regime="CHOP",
                pnl=pnl,
            )

            self.ai.meta_learning.update(pnl)
            self.ai.risk.update_after_trade(
                pnl=pnl,
                equity=state["total_equity"],
            )

            # Reset lifecycle
            self._position_lock = False
            self._peak_price = None
            self._entry_time = None

            state["active_order_id"] = None
            state["execution_state"] = "IDLE"
            state["order_pending"] = False

        self._last_position = current_position
        self._last_qty = state["qty"]
        self._last_entry = state["entry_price"]

    # =========================================================
    # 🔥 EXECUTION ENGINE
    # =========================================================
    def _execute(self, action, price, strategy, regime, confidence, volatility):
        try:
            now = time.time()

            if not self._market_open():
                print("[BLOCK] Market closed")
                return

            if state["execution_state"] == "COOLDOWN":
                if now - state["last_order_time"] < 5:
                    return
                state["execution_state"] = "IDLE"

            if state["execution_state"] == "PENDING":
                if now - state["last_order_time"] > 15:
                    state["execution_state"] = "COOLDOWN"
                    state["last_order_time"] = now
                    state["active_order_id"] = None
                    state["order_pending"] = False
                    self._position_lock = False
                else:
                    return

            if action == "HOLD":
                return

            # Prevent duplicate orders
            orders = self.broker.list_orders()
            active_orders = [
                o for o in orders
                if str(o.get("status", "")).lower() in {"new", "accepted", "pending_new", "partially_filled"}
            ]
            if active_orders:
                return

            # Risk sizing
            if state["position"] != "flat":
                deployable = 0.0
            else:
                deployable = state["equity"]

            risk_pct = self.ai.risk.evaluate(
                action=action,
                confidence=confidence,
                equity=state["total_equity"],
                volatility=volatility,
                strategy=strategy,
                regime=regime,
                performance={
                    "state": "neutral",
                    "margin_pressure": state.get("margin_pressure", 0.0),
                },
                deploy_pct=state.get("deploy_pct", 0.25),
            )

            if risk_pct <= 0:
                return

            max_exposure = state["total_equity"] * state.get("max_exposure_pct", 0.25)
            current_exposure = state["qty"] * price

            # ======================
            # BUY
            # ======================
            if action == "BUY":
                if state["position"] != "flat":
                    return

                if current_exposure >= max_exposure:
                    return

                position_value = deployable * risk_pct
                qty = max(1, int(position_value // price))

                max_affordable = int(state["buying_power"] // price)
                qty = min(qty, max_affordable)

                if qty <= 0:
                    return

                success = self.broker.place_order("SPY", qty, "buy")

                if success:
                    self._entry_time = now
                    self._peak_price = price

                    state["execution_state"] = "PENDING"
                    state["last_order_time"] = now
                    state["last_order_side"] = "BUY"
                    state["order_pending"] = True
                    state["order_timestamp"] = now
                    state["last_action"] = "BUY"

            # ======================
            # SELL
            # ======================
            elif action == "SELL":
                pos = self.broker.get_position("SPY")
                if not pos:
                    return

                available_qty = int(float(pos.get("qty_available", 0) or 0))
                if available_qty <= 0:
                    self._cleanup_orders()
                    state["execution_state"] = "COOLDOWN"
                    state["last_order_time"] = now
                    return

                exit_qty = available_qty  # 🔥 FULL EXIT (important)

                success = self.broker.place_order("SPY", exit_qty, "sell")

                if success:
                    state["execution_state"] = "PENDING"
                    state["last_order_time"] = now
                    state["last_order_side"] = "SELL"
                    state["order_pending"] = True
                    state["order_timestamp"] = now
                    state["last_action"] = "SELL"

        except Exception as e:
            state["logs"].append(f"[EXEC ERROR] {e}")

    # =========================================================
    def _cleanup_orders(self):
        try:
            orders = self.broker.list_orders()
            for order in orders:
                self.broker.cancel_order(order["id"])
        except Exception:
            pass

    def _clear_stale_orders(self):
        try:
            orders = self.broker.list_orders()
            for order in orders:
                self.broker.cancel_order(order["id"])
        except Exception:
            pass