from live_trader import LiveTrader
from data_feed import DataFeed
from risk_manager import RiskManager
from ai_core.diagnostics import run_diagnostics
import time

from meta_supervisor.performance_tracker import PerformanceTracker
from meta_supervisor.drift_detector import DriftDetector
from meta_supervisor.retrainer import Retrainer

from system_guardian.health_monitor import HealthMonitor
from system_guardian.broker_watchdog import BrokerWatchdog
from system_guardian.auto_recovery import AutoRecovery

from ai_core.episodic_memory import EpisodicMemory
from ai_core.strategy_embeddings import StrategyEmbeddings
from ai_core.meta_reasoner import MetaReasoner
from ai_core.strategy_optimizer import StrategyOptimizer

# ✅ NEW IMPORTS
from ai_core.reinforcement_meta_optimizer import ReinforcementMetaOptimizer
from ai_core.adaptive_execution_engine import AdaptiveExecutionEngine
from ai_core.sentient_risk_firewall import SentientRiskFirewall  # ✅ Added


def run_system():
    print("🚀 Power Trading System with Multi-Session Strategy Optimizer starting...")

    # Core modules
    trader, feed, risk = LiveTrader(), DataFeed(), RiskManager()

    # Supervisors
    tracker, detector, retrainer = PerformanceTracker(), DriftDetector(), Retrainer()

    # Guardian modules
    health, watchdog, recovery = HealthMonitor(), BrokerWatchdog(), AutoRecovery()

    # Memory & reasoning
    memory_mgr, embeddings, reasoner = EpisodicMemory(), StrategyEmbeddings(), MetaReasoner()

    # Strategy evolution
    optimizer = StrategyOptimizer()
    rmo = ReinforcementMetaOptimizer()
    aee = AdaptiveExecutionEngine()
    firewall = SentientRiskFirewall()  # ✅ Integrated

    pnl_history, current_episode = [], []

    for _ in range(200):
        tick = feed.next_tick()
        if not tick:
            print("⚠️ No tick from data feed — skipping...")
            continue

        if not risk.can_trade():
            print("⚠️ Trading halted – risk limit hit.")
            break

        action = trader.simulate_trade(tick)
        pnl = 10 if action == "buy" else (-5 if action == "sell" else 0)
        conf = 0.8  # placeholder confidence
        eq = risk.update_equity(pnl)

        tracker.log_trade(action, pnl, conf)
        pnl_history.append(pnl)
        current_episode.append({"action": action, "pnl": pnl, "confidence": conf})

        # Episode / checkpoint every 20 ticks
        if len(pnl_history) % 20 == 0:
            stats = tracker.summarize()
            drift = detector.check_drift(pnl_history[-20:])
            retrainer.retrain_if_needed(drift)

            # Store and embed episode
            episode_id = f"episode_{int(time.time())}"
            memory_mgr.store_episode(episode_id, current_episode)
            emb_vec = embeddings.embed_episode(current_episode)
            embeddings.save_embedding(episode_id, emb_vec)

            insight = reasoner.analyze()
            print(f"📊 Stats: {stats} | Drift={drift} | Insight: {insight}")

            # ✅ Every 3 episodes → optimize strategy
            if (len(pnl_history) // 20) % 3 == 0:
                strategy = optimizer.optimize()
                print(f"🎯 Multi-Session Strategy Optimized: {strategy}")

            # ✅ Every 5 episodes → evolve policies + execute best
            if (len(pnl_history) // 20) % 5 == 0:
                evolved = rmo.evolve_policies(generations=3)
                print(f"🧬 Reinforcement Meta-Optimizer result: {evolved}")

                exec_result = aee.execute(evolved)
                print(f"⚡ Adaptive Execution -> {exec_result}")

                # ✅ 🔒 Sentient Risk Firewall check
                try:
                    decision = firewall.check_trade(exec_result)
                    print(f"🧠 Risk Firewall Decision: {decision}")
                except Exception as e:
                    print(f"⚠️ Firewall check failed: {e}")
                    decision = {"action": "ALLOW"}

                if decision.get("action") == "HALT_TRADING":
                    print("🚫 Firewall halt triggered – pausing execution cycle.")
                    break
                elif decision.get("action") == "THROTTLE":
                    print("⚠️ Firewall throttle – cooldown activated.")
                    time.sleep(decision.get("cooldown", 2))

            current_episode = []

        # ✅ Auto-reactivate when safe
        try:
            firewall.heartbeat()
        except Exception as e:
            print(f"⚠️ Firewall heartbeat error: {e}")

        # ✅ Guardian checks
        try:
            system_alerts = health.check_system()
            broker_status = watchdog.check_brokers()
            recovery_actions = recovery.recover(system_alerts, broker_status)
            for act in recovery_actions:
                print(f"⚠️ {act}")
        except Exception as e:
            print(f"Guardian error: {e}")

    print("✅ Multi-Session Strategy Optimizer cycle complete.")


if __name__ == "__main__":
    run_system()
