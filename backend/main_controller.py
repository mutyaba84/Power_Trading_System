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

        # Trade lifecycle
        self._peak_price = None
        self._entry_time = None

        # Filters
        self._last_price = None
        self._last_trade_time = 0
        self._last_entry_price = None  # 🔥 IMPORTANT (prevents attribute errors)

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

                # -------------------------
                # SYNC
                # -------------------------
                sync_with_broker(state, self.broker)
                update_pnl(state)

                if not state.get("sync_ok", True):
                    print("[BLOCK] Sync unstable -> trading paused")
                    time.sleep(1)
                    continue

                # -------------------------
                # TRADE CLOSE DETECTION
                # -------------------------
                self._detect_trade_close(price)

                # -------------------------
                # POSITION MANAGEMENT
                # -------------------------
                exit_signal = self._manage_position(price)
                if exit_signal:
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

                # -------------------------
                # AI DECISION
                # -------------------------
                action, strategy, regime, confidence, volatility = self.ai.decide_action(
                    price,
                    state["equity"],
                )

                print(f"[AI] action={action} conf={confidence:.2f}")

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
        if not entry:
            return None

        pnl_pct = (price - entry) / entry

        if self._peak_price is None:
            self._peak_price = price
        else:
            self._peak_price = max(self._peak_price, price)

        drawdown = (self._peak_price - price) / self._peak_price

        if pnl_pct <= -0.01:
            print(f"[EXIT] STOP_LOSS | pnl={pnl_pct:.4f}")
            return "STOP_LOSS"

        if pnl_pct >= 0.02:
            print(f"[EXIT] TAKE_PROFIT | pnl={pnl_pct:.4f}")
            return "TAKE_PROFIT"

        if pnl_pct > 0.01 and drawdown > 0.005:
            print(f"[EXIT] TRAILING_STOP | pnl={pnl_pct:.4f}")
            return "TRAILING_STOP"

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
                "duration": time.time() - self._entry_time if self._entry_time else 0
            })

            self._peak_price = None
            self._entry_time = None

            state["execution_state"] = "IDLE"
            state["order_pending"] = False

        self._last_position = current_position
        self._last_qty = state["qty"]
        self._last_entry = state["entry_price"]

    # =========================================================
    # EXECUTION ENGINE
    # =========================================================
    def _execute(self, action, price, strategy, regime, confidence, volatility):
        try:
            now = time.time()

            if not self._market_open():
                return

            if state["execution_state"] == "PENDING":
                if now - state["last_order_time"] < 15:
                    return
                state["execution_state"] = "IDLE"

            if action == "HOLD":
                return

            # -------------------------
            # NOISE FILTER
            # -------------------------
            if self._last_price:
                move = abs(price - self._last_price) / self._last_price
                if move < 0.0005:
                    print("[FILTER] Noise")
                    return

            self._last_price = price

            # -------------------------
            # CONFIDENCE FILTER
            # -------------------------
            if confidence < 0.6:
                print("[FILTER] Low confidence")
                return

            # -------------------------
            # COOLDOWN (STRONG)
            # -------------------------
            if now - self._last_trade_time < 30:
                print("[FILTER] Cooldown")
                return

            # -------------------------
            # PRICE ZONE FILTER
            # -------------------------
            if self._last_entry_price:
                zone = abs(price - self._last_entry_price) / self._last_entry_price
                if zone < 0.001:
                    print("[FILTER] Same zone")
                    return

            # -------------------------
            # EXECUTION
            # -------------------------
            if action == "BUY" and state["position"] == "flat":
                qty = max(1, int(state["equity"] * 0.01 // price))

                if self.broker.place_order("SPY", qty, "buy"):
                    self._entry_time = now
                    self._peak_price = price
                    self._last_trade_time = now
                    self._last_entry_price = price

                    state["execution_state"] = "PENDING"
                    state["last_action"] = "BUY"

            elif action == "SELL" and state["position"] != "flat":
                if self.broker.place_order("SPY", state["qty"], "sell"):
                    self._last_trade_time = now

                    state["execution_state"] = "PENDING"
                    state["last_action"] = "SELL"

        except Exception as e:
            state["logs"].append(f"[EXEC ERROR] {e}")

    def _clear_stale_orders(self):
        try:
            orders = self.broker.list_orders()
            for o in orders:
                self.broker.cancel_order(o["id"])
        except Exception:
            pass