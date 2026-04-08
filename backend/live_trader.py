from backend.ai_core.regime_classifier import RegimeClassifier
from backend.services.strategy_allocator import StrategyAllocator
from backend.ai_core.strategy_gate import StrategyGate
from backend.ai_core.learning_engine import LearningEngine
from backend.ai_core.neural_market_sentiment import NeuralMarketSentiment
from backend.ai_core.meta_reasoner import MetaReasoner
from backend.risk.risk_governor import RiskGovernor
from backend.ai_core.strategy_performance import StrategyPerformance
from backend.services.strategy_tracker import StrategyTracker


class LiveTrader:

    def __init__(self):
        self.regime = RegimeClassifier()
        self.tracker = StrategyTracker()
        self.allocator = StrategyAllocator(self.tracker)
        self.gate = StrategyGate()
        self.performance = StrategyPerformance()

        self.engine = LearningEngine()
        self.sentiment = NeuralMarketSentiment()
        self.meta = MetaReasoner()

        self.risk = RiskGovernor()

        self.prev_price = None

    def decide_action(self, price: float, equity: float):

        try:
            # -------------------------
            # REGIME
            # -------------------------
            regime = self.regime.update(price)

            # 🔥 FIX 1: Ensure tradable regime
            if regime == "UNKNOWN":
                regime = "CHOP"

            # -------------------------
            # STRATEGY
            # -------------------------
            strategy = self.allocator.select(regime)

            # -------------------------
            # GATE
            # -------------------------
            if not self.gate.allowed(strategy, regime):
                return "HOLD", strategy, regime

            # -------------------------
            # SENTIMENT
            # -------------------------
            sentiment = self.sentiment.infer(
                price=price,
                prev_price=self.prev_price
            )

            volatility = sentiment.get("volatility", 0.1)

            # -------------------------
            # AI DECISION
            # -------------------------
            decision_data = self.engine.decide({
                "price": price,
                "volatility": volatility
            })

            action = decision_data.get("decision", "hold").upper()
            confidence = decision_data.get("confidence", 0.5)

            # -------------------------
            # 🔥 FIX 2: Break HOLD deadlock
            # -------------------------
            if action == "HOLD" and confidence > 0.55:
                action = "BUY"

            # -------------------------
            # 🔥 FIX 3: FALLBACK TRADING LOGIC (CRITICAL)
            # -------------------------
            if action == "HOLD" and self.prev_price is not None:
                delta = price - self.prev_price

                if delta < -0.05:
                    action = "BUY"
                elif delta > 0.05:
                    action = "SELL"

            # -------------------------
            # 🔥 FIX 4: Prevent invalid outputs
            # -------------------------
            if action not in ["BUY", "SELL", "HOLD"]:
                action = "HOLD"

            # -------------------------
            # RISK
            # -------------------------
            risk_pct = self.risk.evaluate(
                action=action,
                confidence=confidence,
                equity=equity,
                volatility=volatility,
                strategy=strategy,
            )

            # 🔥 FIX 5: Soften risk blocking
            if risk_pct <= 0:
                if not (action == "BUY" and confidence > 0.6):
                    return "HOLD", strategy, regime

            # -------------------------
            # META (optional)
            # -------------------------
            _ = self.meta.analyze(10)

            # -------------------------
            # DEBUG LOGGING
            # -------------------------
            print(
                f"[AI DEBUG] regime={regime} "
                f"strat={strategy} action={action} "
                f"conf={confidence:.2f} vol={volatility:.2f}"
            )

            # -------------------------
            # UPDATE PRICE MEMORY (IMPORTANT)
            # -------------------------
            self.prev_price = price

            return action, strategy, regime

        except Exception as e:
            print(f"[AI ERROR] {e}")
            return "HOLD", "none", "UNKNOWN"