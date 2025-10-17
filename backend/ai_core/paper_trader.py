"""
Paper Trader
------------
Simulates trading based on Integrative Decision Kernel outputs.
Tracks positions, P&L, equity, and logs all trades.
Updates RL memory loop for learning from simulated outcomes.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from ai_core.integrative_decision_kernel import IntegrativeDecisionKernel
from ai_core.rl_memory_loop import RLMemoryLoop

EXTERNAL_MEMORY = Path("/app/external_memory")
AI_STATE_DIR = EXTERNAL_MEMORY / "ai_state"
LOG_FILE = EXTERNAL_MEMORY / "logs" / "paper_trading.log"

AI_STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

class PaperTrader:
    def __init__(self, starting_equity=100000):
        self.kernel = IntegrativeDecisionKernel()
        self.rl = RLMemoryLoop()
        self.equity = starting_equity
        self.positions = 0.0
        self.trades = []
        self.log("PaperTrader initialized.")

    def log(self, msg):
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

    def simulate_price_movement(self):
        """Generate a pseudo price return for the period"""
        return random.uniform(-0.005, 0.005)  # +/-0.5% per tick

    def run_once(self):
        """Run one paper trading step"""
        decision = self.kernel.compute_action()
        action_score = decision["action_score"]
        confidence = decision["scaled_confidence"]

        # Determine position size (max 50% of equity)
        position_change = self.equity * 0.5 * action_score * confidence

        # Update positions
        self.positions += position_change
        # Simulate price change
        price_return = self.simulate_price_movement()
        pnl = self.positions * price_return
        self.equity += pnl

        # Log trade
        trade_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_score": action_score,
            "confidence": confidence,
            "position": self.positions,
            "pnl": pnl,
            "equity": self.equity
        }
        self.trades.append(trade_record)
        self._save_state()
        self.log(f"Trade executed: Score={action_score:+.3f} | Conf={confidence:.3f} | PnL={pnl:+.2f} | Equity={self.equity:.2f}")

    def _save_state(self):
        with (AI_STATE_DIR / "paper_trading_state.json").open("w", encoding="utf-8") as f:
            json.dump(self.trades[-50:], f, indent=2)  # Keep last 50 trades for reference

    def run_loop(self, steps=100):
        for _ in range(steps):
            self.run_once()

if __name__ == "__main__":
    trader = PaperTrader()
    trader.run_loop(steps=50)
    print("Paper Trading Simulation Completed. Last Equity:", trader.equity)
