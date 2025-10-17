from live_trader import LiveTrader
from data_feed import DataFeed
from risk_manager import RiskManager
from ai_core.diagnostics import run_diagnostics
import time

from meta_supervisor.performance_tracker import PerformanceTracker
from meta_supervisor.drift_detector import DriftDetector
from meta_supervisor.retrainer import Retrainer
# ...existing imports...
from system_guardian.health_monitor import HealthMonitor
from system_guardian.broker_watchdog import BrokerWatchdog
from system_guardian.auto_recovery import AutoRecovery

from ai_core.episodic_memory import EpisodicMemory
from ai_core.strategy_embeddings import StrategyEmbeddings
from ai_core.meta_reasoner import MetaReasoner

def run_system():
    print("🚀 Power Trading System with Episodic Memory AI starting...")
    trader, feed, risk = LiveTrader(), DataFeed(), RiskManager()
    tracker, detector, retrainer = PerformanceTracker(), DriftDetector(), Retrainer()
    health, watchdog, recovery = HealthMonitor(), BrokerWatchdog(), AutoRecovery()
    memory_mgr, embeddings, reasoner = EpisodicMemory(), StrategyEmbeddings(), MetaReasoner()
    pnl_history, current_episode = [], []

    for _ in range(100):
        tick = feed.next_tick()
        if not risk.can_trade(): break

        action = trader.simulate_trade(tick)
        pnl = 10 if action=="buy" else (-5 if action=="sell" else 0)
        conf = 0.8
        eq = risk.update_equity(pnl)

        tracker.log_trade(action, pnl, conf)
        pnl_history.append(pnl)
        current_episode.append({"action": action, "pnl": pnl, "confidence": conf})

        if len(pnl_history) % 20 == 0:
            stats = tracker.summarize()
            drift = detector.check_drift(pnl_history[-20:])
            retrainer.retrain_if_needed(drift)
            memory_mgr.store_episode(f"episode_{int(time.time())}", current_episode)
            emb_vec = embeddings.embed_episode(current_episode)
            embeddings.save_embedding(f"episode_{int(time.time())}", emb_vec)
            insight = reasoner.analyze()
            print(f"📊 Stats: {stats} | Drift={drift} | Insight: {insight}")
            current_episode = []

        system_alerts = health.check_system()
        broker_status = watchdog.check_brokers()
        recovery_actions = recovery.recover(system_alerts, broker_status)
        for act in recovery_actions:
            print(f"⚠️ {act}")

    print("✅ Episodic Memory + Meta-Reasoning cycle complete.")
