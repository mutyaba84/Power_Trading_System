class MetaLearning:
    """
    Controls system behavior based on recent performance
    """

    def __init__(self):
        self.recent_rewards = []
        self.window = 20  # last N trades

        self.performance = "neutral"

    # -------------------------
    def update(self, reward: float):
        self.recent_rewards.append(reward)

        if len(self.recent_rewards) > self.window:
            self.recent_rewards.pop(0)

        avg = sum(self.recent_rewards) / len(self.recent_rewards)

        if avg > 0.2:
            self.performance = "hot"
        elif avg < -0.2:
            self.performance = "cold"
        else:
            self.performance = "neutral"

    # -------------------------
    def get_state(self):
        return self.performance