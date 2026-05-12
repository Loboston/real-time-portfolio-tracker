import asyncio
import random
from decimal import Decimal

import httpx
import structlog

from app.market_data.base import MarketDataProvider

logger = structlog.get_logger(__name__)

_FALLBACK_PRICES: dict[str, Decimal] = {
    "AAPL": Decimal("189.00"),
    "GOOGL": Decimal("175.00"),
    "MSFT": Decimal("415.00"),
    "AMZN": Decimal("185.00"),
    "TSLA": Decimal("175.00"),
    "NVDA": Decimal("875.00"),
    "META": Decimal("500.00"),
    "SPY": Decimal("520.00"),
}

_DEFAULT_FALLBACK = Decimal("100.00")


class PolygonProvider(MarketDataProvider):
    """
    Fetches real previous-close prices from Polygon.io (free tier).
    Seeds each symbol once on first use, then applies small drift each tick
    to simulate intraday movement.
    """

    BASE_URL = "https://api.polygon.io"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._prices: dict[str, Decimal] = {}

    async def _fetch_real_price(self, symbol: str) -> Decimal | None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/v2/aggs/ticker/{symbol}/prev",
                    params={"adjusted": "true", "apiKey": self._api_key},
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        return Decimal(str(results[0]["c"]))
        except Exception:
            logger.warning("failed to fetch price from polygon", symbol=symbol)
        return None

    async def _seed_symbol(self, symbol: str) -> None:
        real_price = await self._fetch_real_price(symbol)
        if real_price:
            logger.info("seeded price from polygon", symbol=symbol, price=str(real_price))
            self._prices[symbol] = real_price
        else:
            fallback = _FALLBACK_PRICES.get(symbol, _DEFAULT_FALLBACK)
            logger.warning("using fallback price", symbol=symbol, price=str(fallback))
            self._prices[symbol] = fallback

    async def fetch_prices(self, symbols: set[str]) -> dict[str, Decimal]:
        # Seed any new symbols concurrently
        unseen = [s for s in symbols if s not in self._prices]
        if unseen:
            await asyncio.gather(*[self._seed_symbol(s) for s in unseen])

        result = {}
        for symbol in symbols:
            if symbol not in self._prices:
                continue

            current = self._prices[symbol]
            drift = Decimal(str(random.uniform(-0.005, 0.005)))
            new_price = (current * (1 + drift)).quantize(Decimal("0.01"))
            new_price = max(new_price, Decimal("0.01"))

            self._prices[symbol] = new_price
            result[symbol] = new_price

        return result
