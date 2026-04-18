from backend.ai_core.regime_classifier import RegimeClassifier
from backend.services.strategy_allocator import StrategyAllocator
from backend.ai_core.strategy_gate import StrategyGate
from backend.ai_core.learning_engine import LearningEngine
from backend.ai_core.neural_market_sentiment import NeuralMarketSentiment
from backend.ai_core.meta_reasoner import MetaReasoner
from backend.risk.risk_governor import RiskGovernor
from backend.ai_core.strategy_performance import StrategyPerformance
from backend.services.strategy_tracker import StrategyTracker
from backend.ai_core.trade_scorer import TradeScorer
from backend.ai_core.meta_learning import MetaLearning
from backend.ai_core.strategy_evolution import StrategyEvolution

from backend.core.state import state


class LiveTrader:

    def __init__(self):
        self.regime = RegimeClassifier()
        self.tracker = StrategyTracker()

        self.allocator = StrategyAllocator(self.tracker)
        self.performance = StrategyPerformance()
        self.gate = StrategyGate()

        self.engine = LearningEngine()
        self.sentiment = NeuralMarketSentiment()

        self.meta_reasoner = MetaReasoner()
        self.meta_learning = MetaLearning()

        self.scorer = TradeScorer()
        self.risk = RiskGovernor()

        self.prev_price = None
        self.strategy_evo = StrategyEvolution()

        # 🔥 NEW: anti-spam memory
        self.last_action = None

    # -----------------------------------
    # MAIN DECISION ENGINE
    # -----------------------------------
    def decide_action(self, price: float, equity: float):

        try:
            # -------------------------
            # 🔥 HARD BLOCK: execution state
            # -------------------------
            if state.get("execution_state") in ["PENDING", "COOLDOWN"]:
                print("[BLOCK] Execution busy")
                return "HOLD", "none", "UNKNOWN", 0.0, 0.0

            # -------------------------
            # REGIME
            # -------------------------
            regime = self.regime.update(price)
            if regime == "UNKNOWN":
                regime = "CHOP"

            # -------------------------
            # STRATEGY SELECTION
            # -------------------------
            strategy = self.allocator.select(regime) or "mean_reversion"

            # -------------------------
            # MARGIN SAFETY
            # -------------------------
            margin_pressure = state.get("margin_pressure", 0)

            if margin_pressure > 0.9 and state["position"] == "long":
                return "SELL", strategy, regime, 1.0, 0.5

            if margin_pressure > 0.8 and state["position"] == "long":
                return "SELL", strategy, regime, 0.9, 0.4

            # -------------------------
            # STRATEGY GATING
            # -------------------------
            if not self.gate.allowed(strategy, regime):
                return "HOLD", strategy, regime, 0.0, 0.0

            if not self.strategy_evo.should_trade(strategy):
                return "HOLD", strategy, regime, 0.0, 0.0

            # -------------------------
            # SENTIMENT
            # -------------------------
            sentiment = self.sentiment.infer(
                price=price,
                prev_price=self.prev_price
            )

            volatility = sentiment.get("volatility", 0.1)

            # -------------------------
            # AI CORE DECISION
            # -------------------------
            decision_data = self.engine.decide({
                "price": price,
                "volatility": volatility
            })

            action = decision_data.get("decision", "hold").upper()
            confidence = decision_data.get("confidence", 0.5)

            # -------------------------
            # CONFIDENCE FILTER
            # -------------------------
            MIN_CONFIDENCE = self.scorer.get_dynamic_threshold(regime)

            if confidence < MIN_CONFIDENCE:
                action = "HOLD"

            # -------------------------
            # LOW VOL FILTER
            # -------------------------
            if volatility < 0.08:
                return "HOLD", strategy, regime, 0.0, volatility

            # -------------------------
            # MOMENTUM FILTER
            # -------------------------
            momentum = 0.0

            if self.prev_price is not None:
                momentum = price - self.prev_price

                if action == "BUY" and momentum <= 0:
                    action = "HOLD"

                if action == "SELL" and momentum >= 0:
                    action = "HOLD"

            # -------------------------
            # 🔥 POSITION-AWARE FILTER
            # -------------------------
            if state["position"] == "long" and action == "BUY":
                action = "HOLD"

            if state["position"] == "flat" and action == "SELL":
                action = "HOLD"

            # -------------------------
            # 🔥 ANTI-SPAM FILTER
            # -------------------------
            if action == self.last_action:
                return "HOLD", strategy, regime, 0.0, volatility

            # -------------------------
            # FINAL VALIDATION
            # -------------------------
            if action not in ["BUY", "SELL"]:
                self.prev_price = price
                return "HOLD", strategy, regime, 0.0, volatility

            # -------------------------
            # STORE STATE
            # -------------------------
            self.prev_price = price
            self.last_action = action

            return action, strategy, regime, confidence, volatility

        except Exception as e:
            print(f"[AI ERROR] {e}")
            return "HOLD", "mean_reversion", "CHOP", 0.0, 0.0