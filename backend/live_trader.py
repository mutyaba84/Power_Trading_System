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


class LiveTrader:

    def __init__(self):
        # Core systems
        self.regime = RegimeClassifier()
        self.tracker = StrategyTracker()
        self.allocator = StrategyAllocator(self.tracker)
        self.gate = StrategyGate()
        self.performance = StrategyPerformance()

        # AI systems
        self.engine = LearningEngine()
        self.sentiment = NeuralMarketSentiment()

        # 🔥 BOTH meta systems (fixed)
        self.meta_reasoner = MetaReasoner()
        self.meta_learning = MetaLearning()

        # Decision + risk
        self.scorer = TradeScorer()
        self.risk = RiskGovernor()

        self.prev_price = None
        self.strategy_evo = StrategyEvolution()

    def decide_action(self, price: float, equity: float):

        try:
            # -------------------------
            # REGIME DETECTION
            # -------------------------
            regime = self.regime.update(price)
            if regime == "UNKNOWN":
                regime = "CHOP"

            # -------------------------
            # STRATEGY SELECTION
            # -------------------------
            strategy = self.allocator.select(regime)

            # -------------------------
            # STRATEGY GATE
            # -------------------------
            if not self.gate.allowed(strategy, regime):
                return "HOLD", strategy, regime



            #--------------------------
            # STRATEGY FILTER (NEW)
            #--------------------------
            if not self.strategy_evo.should_trade(strategy):
                print(f"[STRATEGY BLOCKED] {strategy} blocked by evolution")
                return "HOLD", strategy, regime

            # -------------------------
            # MARKET SENTIMENT
            # -------------------------
            sentiment = self.sentiment.infer(
                price=price,
                prev_price=self.prev_price
            )

            volatility = sentiment.get("volatility", 0.1)

            # -------------------------
            # AI DECISION ENGINE
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
            MIN_CONFIDENCE = 0.6 if regime != "CHOP" else 0.65

            if confidence < MIN_CONFIDENCE:
                action = "HOLD"

            # -------------------------
            # VOLATILITY FILTER
            # -------------------------
            if volatility < 0.08:
                return "HOLD", strategy, regime

            # -------------------------
            # MOMENTUM FILTER
            # -------------------------
            momentum = 0.0
            momentum_pct = 0.0

            if self.prev_price is not None:
                momentum = price - self.prev_price

                if price != 0:
                    momentum_pct = momentum / price

                if action == "BUY" and momentum_pct <= 0:
                    action = "HOLD"

                if action == "SELL" and momentum_pct >= 0:
                    action = "HOLD"

            # -------------------------
            # VALIDATE ACTION
            # -------------------------
            if action not in ["BUY", "SELL"]:
                self.prev_price = price
                return "HOLD", strategy, regime

            # -------------------------
            # 🚀 TRADE SCORING
            # -------------------------
            score = self.scorer.score(
                confidence=confidence,
                momentum=momentum,
                volatility=volatility,
                regime=regime,
                price=price
            )

            # 🔥 META PERFORMANCE STATE
            performance_state = self.meta_learning.get_state()

            if not self.scorer.allow_trade(score, regime, performance_state):
                print(f"[FILTER] rejected | score={score:.2f} perf={performance_state}")
                self.prev_price = price
                return "HOLD", strategy, regime

            # -------------------------
            # 💰 RISK EVALUATION
            # -------------------------
            risk_pct = self.risk.evaluate(
                action=action,
                confidence=confidence,
                equity=equity,
                volatility=volatility,
                strategy=strategy,
                regime=regime,
                performance=performance_state
            )

            if risk_pct <= 0:
                self.prev_price = price
                return "HOLD", strategy, regime

            # -------------------------
            # META REASONER (optional intelligence)
            # -------------------------
            _ = self.meta_reasoner.analyze(10)

            # -------------------------
            # DEBUG OUTPUT
            # -------------------------
            print(
                f"[AI DEBUG] regime={regime} strat={strategy} action={action} "
                f"conf={confidence:.2f} vol={volatility:.2f} "
                f"mom={momentum_pct:.5f} score={score:.2f} "
                f"risk={risk_pct:.4f} perf={performance_state}"
            )

            # -------------------------
            # MEMORY UPDATE
            # -------------------------
            self.prev_price = price

            return action, strategy, regime

        except Exception as e:
            print(f"[AI ERROR] {e}")
            return "HOLD", "none", "UNKNOWN"