import time
from typing import Any, Dict, Optional

from backend.utils.event_log import log_event
from backend.utils.logger import get_logger

from backend.live_trader import LiveTrader
from backend.data_feed import DataFeed
from backend.risk_manager import RiskManager


def _safe_import(path: str):
    try:
        mod_path, name = path.rsplit(".", 1)
        mod = __import__(mod_path, fromlist=[name])
        return getattr(mod, name)
    except Exception:
        return None


PerformanceTracker = _safe_import("backend.meta_supervisor.performance_tracker.PerformanceTracker")
DriftDetector = _safe_import("backend.meta_supervisor.drift_detector.DriftDetector")
Retrainer = _safe_import("backend.meta_supervisor.retrainer.Retrainer")

HealthMonitor = _safe_import("backend.system_guardian.health_monitor.HealthMonitor")
BrokerWatchdog = _safe_import("backend.system_guardian.broker_watchdog.BrokerWatchdog")
AutoRecovery = _safe_import("backend.system_guardian.auto_recovery.AutoRecovery")

EpisodicMemory = _safe_import("backend.ai_core.episodic_memory.EpisodicMemory")
StrategyEmbeddings = _safe_import("backend.ai_core.strategy_embeddings.StrategyEmbeddings")
MetaReasoner = _safe_import("backend.ai_core.meta_reasoner.MetaReasoner")
StrategyOptimizer = _safe_import("backend.ai_core.strategy_optimizer.StrategyOptimizer")

ReinforcementMetaOptimizer = _safe_import("backend.ai_core.reinforcement_meta_optimizer.ReinforcementMetaOptimizer")
AdaptiveExecutionEngine = _safe_import("backend.ai_core.adaptive_execution_engine.AdaptiveExecutionEngine")
SentientRiskFirewall = _safe_import("backend.ai_core.sentient_risk_firewall.SentientRiskFirewall")

logger = get_logger("main_controller")


class TradingController:
    """
    One orchestrator loop:
      - fetch tick
      - risk check + size
      - trader action
      - register trade + events
      - periodic checkpoint work
    """

    def __init__(self) -> None:
        self.trader = LiveTrader()
        self.feed = DataFeed()
        self.risk = RiskManager()

        self.tracker = PerformanceTracker() if PerformanceTracker else None
        self.detector = DriftDetector() if DriftDetector else None
        self.retrainer = Retrainer() if Retrainer else None

        self.health = HealthMonitor() if HealthMonitor else None
        self.watchdog = BrokerWatchdog() if BrokerWatchdog else None
        self.recovery = AutoRecovery() if AutoRecovery else None

        self.memory_mgr = EpisodicMemory() if EpisodicMemory else None
        self.embeddings = StrategyEmbeddings() if StrategyEmbeddings else None
        self.reasoner = MetaReasoner() if MetaReasoner else None
        self.optimizer = StrategyOptimizer() if StrategyOptimizer else None

        self.rmo = ReinforcementMetaOptimizer() if ReinforcementMetaOptimizer else None
        self.aee = AdaptiveExecutionEngine() if AdaptiveExecutionEngine else None
        self.firewall = SentientRiskFirewall() if SentientRiskFirewall else None

        self.pnl_history = []
        self.current_episode = []
        self.tick_count = 0
        self.checkpoint_count = 0

        self.halt_reason: Optional[str] = None

    def step(self) -> Optional[Dict[str, Any]]:
        tick = self.feed.next_tick()
        if not tick:
            log_event("feed.empty")
            return None

        price = tick.get("price")
        if price is None:
            log_event("tick.invalid", reason="missing_price")
            return None

        if not self.risk.can_trade():
            self.halt_reason = "risk_halt"
            log_event("system.halt", reason=self.halt_reason)
            return {"event": "system.halt", "reason": self.halt_reason}

        # Placeholder confidence until model is wired
        confidence = 0.8

        sizing = self.risk.position_size(confidence=confidence)

        if (not getattr(sizing, "allowed", False)) or getattr(sizing, "size", 0) <= 0:
            action = "hold"
            pnl = 0.0
            self.risk.register_trade(
                action=action,
                pnl=pnl,
                size=0.0,
                price=float(price),
            )
        else:
            action = self.trader.simulate_trade(tick, trade_size=float(sizing.size))

            # Placeholder pnl model (replace later with execution fills)
            pnl = 10.0 if action == "buy" else (-5.0 if action == "sell" else 0.0)

            self.risk.register_trade(
                action=action,
                pnl=pnl,
                size=float(sizing.size),
                price=float(price),
            )

        self.pnl_history.append(pnl)
        self.current_episode.append({"action": action, "pnl": pnl, "confidence": confidence})

        # IMPORTANT: do NOT include key named "event" in **kwargs for log_event()
        payload = {
            "tick": self.tick_count,
            "action": action,
            "pnl": pnl,
            "confidence": confidence,
            "equity": float(getattr(self.risk, "equity", 0.0)),
            "price": float(price),
        }

        log_event("tick.processed", **payload)

        # return structure for UI/callers
        event = {"event": "tick.processed", **payload}

        if self.tracker:
            try:
                self.tracker.log_trade(action, pnl, confidence)
            except Exception as e:
                log_event("tracker.error", error=str(e))

        self.tick_count += 1
        return event

    def checkpoint(self) -> None:
        """
        Runs every 20 ticks from run loop.
        """
        self.checkpoint_count += 1
        log_event("checkpoint.start", n=self.checkpoint_count)

        # Drift + retrain
        if self.detector and self.retrainer and len(self.pnl_history) >= 20:
            try:
                drift = self.detector.check_drift(self.pnl_history[-20:])
                log_event("meta.drift", drift=drift)
                self.retrainer.retrain_if_needed(drift)
            except Exception as e:
                log_event("meta.error", error=str(e))

        # Episodic memory
        if self.memory_mgr and self.embeddings and self.reasoner and self.current_episode:
            try:
                episode_id = f"episode_{int(time.time())}"
                self.memory_mgr.store_episode(episode_id, self.current_episode)
                vec = self.embeddings.embed_episode(self.current_episode)
                self.embeddings.save_embedding(episode_id, vec)
                insight = self.reasoner.analyze()
                log_event("memory.episode", episode_id=episode_id)
                log_event("reasoner.insight", insight=str(insight))
            except Exception as e:
                log_event("memory.error", error=str(e))

        # Strategy optimizer every 3 checkpoints
        if self.optimizer and (self.checkpoint_count % 3 == 0):
            try:
                strat = self.optimizer.optimize()
                log_event("strategy.optimized", strategy=str(strat))
            except Exception as e:
                log_event("strategy.error", error=str(e))

        # RMO every 5 checkpoints
        if self.rmo and self.aee and (self.checkpoint_count % 5 == 0):
            try:
                evolved = self.rmo.evolve_policies(generations=3)
                exec_result = self.aee.execute(evolved)

                decision = {"action": "ALLOW"}
                if self.firewall:
                    decision = self.firewall.check_trade(exec_result)

                log_event("execution.result", result=str(exec_result))
                log_event("firewall.decision", decision=decision)

                if isinstance(decision, dict) and decision.get("action") == "HALT_TRADING":
                    self.halt_reason = "firewall_halt"
                    log_event("system.halt", reason=self.halt_reason)
            except Exception as e:
                log_event("execution.error", error=str(e))

        # Guardian checks
        if self.health and self.watchdog and self.recovery:
            try:
                alerts = self.health.check_system()
                brokers = self.watchdog.check_brokers()
                actions = self.recovery.recover(alerts, brokers)
                for act in actions or []:
                    log_event("guardian.action", action=str(act))
            except Exception as e:
                log_event("guardian.error", error=str(e))

        self.current_episode = []
        log_event("checkpoint.done", n=self.checkpoint_count)


def run_system(ticks: int = 200, sleep_s: float = 0.2) -> None:
    logger.info("Power Trading System controller starting...")
    log_event("system.start", mode="controller")

    ctl = TradingController()

    for i in range(ticks):
        ev = ctl.step()

        # stop if halt triggered
        if ev and ev.get("event") == "system.halt":
            logger.warning(f"System halt triggered: {ev.get('reason')}")
            break

        if ctl.halt_reason:
            logger.warning(f"System halt triggered: {ctl.halt_reason}")
            break

        if (i + 1) % 20 == 0:
            ctl.checkpoint()

        time.sleep(sleep_s)

    log_event("system.stop", mode="controller", reason=ctl.halt_reason or "normal")
    logger.info("Controller finished.")
