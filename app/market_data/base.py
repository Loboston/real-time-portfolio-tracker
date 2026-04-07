from abc import ABC, abstractmethod
from decimal import Decimal


class MarketDataProvider(ABC):
    """
    Abstract interface for market data providers.
    Swap implementations without changing anything else in the system.
    """

    @abstractmethod
    async def fetch_prices(self, symbols: set[str]) -> dict[str, Decimal]:
        """
        Fetch the latest price for each symbol.
        Returns a dict of {symbol: price} for all symbols successfully retrieved.
        Symbols that fail or are unknown are omitted from the result.
        """
        ...
