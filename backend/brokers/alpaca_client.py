from alpaca_trade_api.rest import REST, TimeFrame
from backend.brokers.alpaca_config import get_alpaca_config

class AlpacaClient:
    def __init__(self):
        cfg = get_alpaca_config()

        self.api = REST(
            key_id=cfg["key_id"],
            secret_key=cfg["secret_key"],
            base_url=cfg["base_url"],
            api_version="v2",
        )

        self.symbol = cfg["symbol"]
        self.timeframe = TimeFrame.Minute

    def ping(self):
        """Hard proof that authentication works"""
        return self.api.get_account()

    def get_latest_bar(self):
        bars = self.api.get_bars(
            self.symbol,
            self.timeframe,
            limit=1
        )
        return bars[0] if bars else None
