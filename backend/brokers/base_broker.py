from abc import ABC, abstractmethod


class BaseBroker(ABC):
    """
    Generic broker interface.
    All brokers (Alpaca, Binance, Simulation, etc.) must follow this contract.
    """

    def __init__(self, mode="simulation"):
        self.mode = mode

    @abstractmethod
    def connect(self):
        """Establish connection with broker"""
        pass

    @abstractmethod
    def place_order(self, symbol, qty, side, order_type="market"):
        """
        Place an order.
        side: 'buy' or 'sell'
        order_type: 'market', 'limit'
        """
        pass

    @abstractmethod
    def get_positions(self):
        """Return current open positions"""
        pass

    @abstractmethod
    def get_account(self):
        """Return account info (cash, equity, buying power)"""
        pass

    # ---------- OPTIONAL SAFETY EXTENSIONS ----------

    def is_live(self):
        """Check if broker is in live trading mode"""
        return self.mode == "live"

    def supports_fractional(self):
        """Override if broker supports fractional shares"""
        return False

    def supports_crypto(self):
        """Override if broker supports crypto trading"""
        return False
