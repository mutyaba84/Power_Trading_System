import time
import threading

from backend.core.state import state
from backend.live_trader import LiveTrader
from backend.brokers.alpaca_broker import AlpacaBroker
from backend.brokers.config import get_alpaca_config
from backend.ai_core.reward_policy import RewardPolicy


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

        self.reward = RewardPolicy()

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

                self._sync_account()
                self._sync_position()

                state["prev_equity"] = state.get("equity")
                state["can_trade"] = state["buying_power"] > 50

                # -------------------------
                # AI DECISION
                # -------------------------
                action, strategy, regime = self.ai.decide_action(
                    price, state["equity"]
                )

                state["strategy"] = strategy

                # -------------------------
                # EXECUTE
                # -------------------------
                self._execute(action, price, strategy)

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

            deploy_pct = state.get("deploy_pct", 0.25)
            deployable = eq * deploy_pct

            state["total_equity"] = eq
            state["deployable_equity"] = deployable
            state["equity"] = deployable
            state["buying_power"] = min(bp, deployable)
            state["cash"] = cash

        except Exception as e:
            state["buying_power"] = 0
            state["logs"].append(f"[ACCOUNT ERROR] {e}")

    # ------------------------
    def _execute(self, action, price, strategy):
        try:
            now = time.time()

            if self.order_in_flight:
                return

            if now - self.last_trade_time < self.cooldown:
                return

            if action == "HOLD":
                return

            qty_held = state["qty"]

            # ------------------------
            # RISK
            # ------------------------
            risk_pct = self.ai.risk.evaluate(
                action=action,
                confidence=0.7,
                equity=state["equity"],
                volatility=0.1,
                strategy=strategy,
                regime="TREND",
                performance=self.ai.meta_learning.get_state()
            )

            # ------------------------
            # STRATEGY WEIGHTING (UPDATED 🔥)
            # ------------------------
            weights = self.ai.strategy_evo.normalize()

            strategy_weight = weights.get(strategy, 0.5)
            strategy_weight = max(0.2, min(strategy_weight, 1.5))

            # smoothing (prevents jumps)
            prev_weight = state.get("last_weight", 1.0)
            strategy_weight = 0.7 * prev_weight + 0.3 * strategy_weight
            state["last_weight"] = strategy_weight

            trade_value = state["deployable_equity"] * risk_pct * strategy_weight

            # ------------------------
            # EXPOSURE LIMIT
            # ------------------------
            MAX_TOTAL_EXPOSURE = state["deployable_equity"]
            current_exposure = qty_held * price

            if action == "BUY" and (current_exposure + trade_value) > MAX_TOTAL_EXPOSURE:
                state["logs"].append("[BLOCK] max exposure reached")
                return

            trade_qty = max(1, int(trade_value // price))

            if trade_qty <= 0:
                return

            self.order_in_flight = True

            # ------------------------
            # BUY
            # ------------------------
            if action == "BUY":
                self.broker.place_order("SPY", trade_qty, "buy")
                state["entry_price"] = price
                state["position"] = "long"

            # ------------------------
            # SELL
            # ------------------------
            elif action == "SELL":
                self.broker.place_order("SPY", qty_held, "sell")

                pnl = 0.0

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

                    # ------------------------
                    # REWARD SYSTEM
                    # ------------------------
                    reward, _ = self.reward.compute_from_dict({
                        "equity": state["equity"],
                        "prev_equity": state.get("prev_equity"),
                        "realized_pnl": pnl,
                        "position_qty": qty_held,
                        "price": price,
                        "trade_count": 1,
                        "ts": time.time()
                    })

                    # ------------------------
                    # LEARNING LOOP
                    # ------------------------
                    self.ai.scorer.update_performance(reward)
                    self.ai.meta_learning.update(reward)
                    self.ai.strategy_evo.update(strategy, reward)

                    state["logs"].append(f"[REWARD] total={reward:.4f}")

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