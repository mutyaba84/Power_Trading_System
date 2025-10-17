from .reward_policy import RewardPolicy
from .strategy_optimizer import StrategyOptimizer
import random, json, numpy as np
from pathlib import Path
import time

class ReinforcementMetaOptimizer:
    def __init__(self, external_memory="/app/external_memory"):
        self.memory_root = Path(external_memory)
        self.policy_dir = self.memory_root / "policies"
        self.sim_dir = self.memory_root / "simulations"
        self.policy_dir.mkdir(parents=True, exist_ok=True)
        self.sim_dir.mkdir(parents=True, exist_ok=True)

        self.reward_policy = RewardPolicy()
        self.strategy_optimizer = StrategyOptimizer()

    def simulate_policy(self, strategy):
        # Generate pseudo trade results based on current strategy
        pnl = [random.gauss(strategy["expected_avg_pnl"], 5) for _ in range(50)]
        drawdown = [abs(p * random.uniform(0.05, 0.3)) for p in pnl]
        return pnl, drawdown

    def evolve_policies(self, generations=5):
        print("⚙️  Reinforcement Meta-Optimizer evolving policies...")

        base_strategy = self.strategy_optimizer.optimize()
        if base_strategy["status"] == "no_data":
            return {"status": "no_base_data"}

        population = [base_strategy.copy() for _ in range(10)]
        for g in range(generations):
            rewards = []
            for policy in population:
                pnl, drawdown = self.simulate_policy(policy)
                reward = self.reward_policy.calculate(pnl, drawdown)
                policy["reward"] = reward
                rewards.append(reward)

            # Select top 3 and mutate
            top = sorted(population, key=lambda x: x["reward"], reverse=True)[:3]
            next_gen = []
            for t in top:
                for _ in range(3):
                    child = t.copy()
                    child["expected_avg_pnl"] += random.uniform(-1, 1)
                    next_gen.append(child)
            population = next_gen

        # Best evolved strategy
        best_policy = max(population, key=lambda x: x["reward"])
        filename = self.policy_dir / f"policy_{int(time.time())}.json"
        filename.write_text(json.dumps(best_policy, indent=2))
        return best_policy
