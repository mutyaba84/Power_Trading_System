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
# True  = allow paper-test orders outside normal market hours
# False = block orders when market is closed
ALLOW_AFTER_HOURS_TESTING = True


class TradingController:

    def __init__(self):
        print("[CONTROLLER] Loaded testing controller v5 - market gate override enabled")

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

            print(
                f"[EXEC] action={action} price={price} "
                f"position={state['position']} sync_ok={state.get('sync_ok')}"
            )

            market_open = self._market_open()

            if not market_open and not ALLOW_AFTER_HOURS_TESTING:
                print("[BLOCK] Market closed")
                return

            if not market_open and ALLOW_AFTER_HOURS_TESTING:
                print("[TEST MODE] Market closed but after-hours testing is enabled")

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

            # =====================================================
            # SELL / EXIT — NEVER APPLY BUY FILTERS HERE
            # =====================================================
            if action in ["SELL", "FULL_EXIT", "PARTIAL_EXIT"]:
                if state["position"] == "flat":
                    print("[SELL BLOCK] Already flat")
                    return

                pos = self.broker.get_position("SPY")
                if not pos:
                    print("[SELL BLOCK] No broker position")
                    return

                available_qty = int(float(pos.get("qty_available", 0) or 0))
                if available_qty <= 0:
                    print("[SELL BLOCK] No available qty")
                    return

                if action == "PARTIAL_EXIT":
                    exit_qty = max(1, available_qty // 2)
                else:
                    exit_qty = available_qty

                print(f"[SELL] action={action} qty={exit_qty}")

                if self.broker.place_order("SPY", exit_qty, "sell"):
                    self._last_trade_time = now

                    state["execution_state"] = "PENDING"
                    state["last_order_time"] = now
                    state["last_order_side"] = "SELL"
                    state["order_pending"] = True
                    state["order_timestamp"] = now
                    state["last_action"] = "SELL"

                return

            # =====================================================
            # BUY — FILTERS APPLY ONLY HERE
            # =====================================================
            if action == "BUY":
                if state["position"] != "flat":
                    print("[BUY BLOCK] Already in position")
                    return

                min_move_pct = 0.00015

                if self._last_price:
                    move = abs(price - self._last_price) / self._last_price

                    if move < min_move_pct:
                        print(f"[FILTER] Noise move={move:.5f}")
                        return

                self._last_price = price

                min_confidence = 0.50

                if confidence < min_confidence:
                    print(f"[FILTER] Low confidence confidence={confidence:.2f}")
                    return

                cooldown_seconds = 12

                if now - self._last_trade_time < cooldown_seconds:
                    remaining = cooldown_seconds - (now - self._last_trade_time)
                    print(f"[FILTER] Cooldown remaining={remaining:.1f}s")
                    return

                zone_limit = 0.0003

                if self._last_entry_price:
                    zone = abs(price - self._last_entry_price) / self._last_entry_price

                    if zone < zone_limit:
                        print(f"[FILTER] Same zone zone={zone:.5f}")
                        return

                qty = max(1, int(state["equity"] * 0.01 // price))

                print(
                    f"[BUY] qty={qty} price={price} "
                    f"confidence={confidence:.2f} equity={state['equity']}"
                )

                if self.broker.place_order("SPY", qty, "buy"):
                    self._entry_time = now
                    self._peak_price = price
                    self._last_trade_time = now
                    self._last_entry_price = price
                    self._scaled_out = False

                    state["execution_state"] = "PENDING"
                    state["last_order_time"] = now
                    state["last_order_side"] = "BUY"
                    state["order_pending"] = True
                    state["order_timestamp"] = now
                    state["last_action"] = "BUY"

                return

        except Exception as e:
            state["logs"].append(f"[EXEC ERROR] {e}")

    def _clear_stale_orders(self):
        try:
            orders = self.broker.list_orders()
            for o in orders:
                self.broker.cancel_order(o["id"])
        except Exception:
            pass