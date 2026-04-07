import random
from decimal import Decimal

from app.market_data.base import MarketDataProvider

# Realistic starting prices for common symbols
_BASE_PRICES: dict[str, Decimal] = {
    "AAPL": Decimal("189.00"),
    "GOOGL": Decimal("175.00"),
    "MSFT": Decimal("415.00"),
    "AMZN": Decimal("185.00"),
    "TSLA": Decimal("175.00"),
    "NVDA": Decimal("875.00"),
    "META": Decimal("500.00"),
    "SPY": Decimal("520.00"),
}

_DEFAULT_PRICE = Decimal("100.00")


class MockMarketDataProvider(MarketDataProvider):
    """
    Simulates a market data feed with small random price drift each tick.
    Prices start at realistic values and move up or down by up to 0.5% per poll.
    """

    def __init__(self) -> None:
        # Track current prices in memory so drift accumulates across ticks
        self._prices: dict[str, Decimal] = {}

    async def fetch_prices(self, symbols: set[str]) -> dict[str, Decimal]:
        result = {}
        for symbol in symbols:
            if symbol not in self._prices:
                self._prices[symbol] = _BASE_PRICES.get(symbol, _DEFAULT_PRICE)

            current = self._prices[symbol]
            drift = Decimal(str(random.uniform(-0.005, 0.005)))
            new_price = (current * (1 + drift)).quantize(Decimal("0.01"))
            new_price = max(new_price, Decimal("0.01"))  # price can't go negative

            self._prices[symbol] = new_price
            result[symbol] = new_price

        return result
