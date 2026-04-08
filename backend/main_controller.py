import time
import threading

from backend.core.state import state
from backend.live_trader import LiveTrader
from backend.brokers.alpaca_broker import AlpacaBroker
from backend.brokers.config import get_alpaca_config


class TradingController:

    def __init__(self):
        self.running = False
        self.ai = LiveTrader()

        cfg = get_alpaca_config()
        print("[INIT] Using Alpaca key:", cfg["api_key"][:6])

        self.broker = AlpacaBroker(
            api_key=cfg["api_key"],
            secret_key=cfg["secret_key"],
            paper=cfg["paper"]
        )

        self.last_trade_time = 0
        self.cooldown = 2
        self.order_in_flight = False
        self.last_account_log = 0

    # ------------------------
    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()
        print("[CONTROLLER] Started")

    def stop(self):
        self.running = False

    # ------------------------
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
                self._sync_account()
                self._sync_position()

                state["can_trade"] = state["buying_power"] > 50

                # -------------------------
                # UNREALIZED PnL
                # -------------------------
                if state["position"] == "long" and state["entry_price"]:
                    state["unrealized_pnl"] = (
                        (price - state["entry_price"]) * state["qty"]
                    )
                else:
                    state["unrealized_pnl"] = 0.0

                # -------------------------
                # AI DECISION
                # -------------------------
                action, strategy, regime = self.ai.decide_action(
                    price, state["equity"]
                )
                # -------------------------
                # 🔥 RISK MANAGEMENT (EXIT LOGIC)
                # -------------------------

                if state ["position"] == "long" and state["entry_price"]:
                    entry = state["entry_price"]
                    pnl_pct = (price - entry) / entry

                    # ----STOP LOSS:  ----
                    
                    if pnl_pct < -0.02:  # 2% stop loss
                        action = "SELL"
                        state["logs"].append(
                            f"[RISK] Stop loss triggered")


                    # ----TAKE PROFIT:  ----
                    elif pnl_pct > 0.02:  # 2% take profit   
                        action = "SELL"
                        state["logs"].append( "[RISK] Take profit triggered"  ) 


                    # ----TRAILER LOCKC(light):  ----
                    elif pnl_pct > 0.01:  # lock profits if price falls back sligthly 
                       if price < entry * 1.05:  # if price retraces more than 0.5% from peak
                            action = "SELL"
                            state["logs"].append(
                                f"[RISK] Trailer lock triggered")



                if action == "SELL" and state["qty"] == 0:
                    action = "HOLD"

                if action == "BUY" and not state["can_trade"]:
                    action = "HOLD"

                # -------------------------
                # EXECUTE
                # -------------------------
                self._execute(action, price)

                state["logs"].append(
                    f"[AI] regime={regime} strat={strategy} action={action}"
                )

            except Exception as e:
                state["logs"].append(f"[CTRL ERROR] {e}")

            time.sleep(1)

    # ------------------------
    def _sync_position(self):
        try:
            pos = self.broker.get_position("SPY")

            if pos and float(pos["qty"]) > 0:
                state["qty"] = int(float(pos["qty"]))
                state["position"] = "long"
            else:
                # prevent immediate flip during broker delay
                if state["position"] != "long":
                    state["qty"] = 0
                    state["position"] = "flat"

        except Exception:
            pass

    # ------------------------
    def _sync_account(self):
        try:
            account = self.broker.get_account()

            bp = float(account.buying_power)
            eq = float(account.equity)
            cash = float(account.cash)

            if bp == 0 and cash > 0:
                bp = cash

            state["buying_power"] = bp
            state["equity"] = eq
            state["cash"] = cash

            if time.time() - self.last_account_log > 5:
                state["logs"].append(f"[ACCOUNT] BP={bp:.2f}")
                self.last_account_log = time.time()

        except Exception as e:
            state["buying_power"] = 0
            state["logs"].append(f"[ACCOUNT ERROR] {e}")

    # ------------------------
    def _execute(self, action, price):
        try:
            now = time.time()

            buying_power = state["buying_power"]
            qty_held = state["qty"]

            state["logs"].append(
                f"[EXEC DEBUG] action={action} qty={qty_held} bp={buying_power:.2f}"
            )

            # ------------------------
            # BASIC GUARDS
            # ------------------------
            if self.order_in_flight:
                return

            if now - self.last_trade_time < self.cooldown:
                return

            if action == "HOLD":
                return

            if action == "SELL" and qty_held == 0:
                return

            if action == "BUY" and not state["can_trade"]:
                return

            # ------------------------
            # POSITION CONTROL
            # ------------------------
            MAX_POSITION_SIZE = 500

            if action == "BUY":
                if state["position"] == "long":
                    state["logs"].append("[BLOCK] already in position")
                    return

                if qty_held >= MAX_POSITION_SIZE:
                    state["logs"].append("[BLOCK] max position reached")
                    return

            # ------------------------
            # RISK CONTROL
            # ------------------------
            risk_pct = 0.01  # 🔥 1% per trade

            trade_value = buying_power * risk_pct
            trade_qty = max(1, int(trade_value // price))

            trade_qty = min(trade_qty, MAX_POSITION_SIZE)

            # ------------------------
            # EXECUTE ORDER
            # ------------------------
            self.order_in_flight = True

            if action == "BUY":
                self.broker.place_order("SPY", trade_qty, "buy")
                state["entry_price"] = price
                state["position"] = "long"

            elif action == "SELL":
                self.broker.place_order("SPY", qty_held, "sell")

                if state["entry_price"]:
                    pnl = (price - state["entry_price"]) * qty_held
                    state["realized_pnl"] += pnl
                    state["trade_count"] += 1

                    if pnl > 0:
                        state["win_count"] += 1
                    else:
                        state["loss_count"] += 1

                    state["trades"].append({
                        "entry": state["entry_price"],
                        "exit": price,
                        "qty": qty_held,
                        "pnl": pnl,
                        "timestamp": time.time()
                    })

                state["entry_price"] = None
                state["position"] = "flat"

            # ------------------------
            # FINALIZE
            # ------------------------
            state["last_action"] = action
            self.last_trade_time = now

            state["logs"].append(
                f"[LIVE TRADE] {action} qty={trade_qty if action=='BUY' else qty_held} @ {price:.2f}"
            )

            self.order_in_flight = False

        except Exception as e:
            self.order_in_flight = False
            state["logs"].append(f"[EXEC ERROR] {e}")