from abc import ABC, abstractmethod

class BaseBroker(ABC):
    """Generic broker interface"""
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def place_order(self, symbol, qty, side, order_type="market"):
        """Place a market or limit order"""
        pass

    @abstractmethod
    def get_positions(self):
        """Return current positions"""
        pass

    @abstractmethod
    def get_account(self):
        """Return account info like equity"""
        pass
