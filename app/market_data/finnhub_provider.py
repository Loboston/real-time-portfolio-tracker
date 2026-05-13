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


class FinnhubProvider(MarketDataProvider):
    """
    Fetches real-time US stock quotes from Finnhub (free tier).
    Returns live prices during market hours, last close price after hours.
    Falls back to cached price on API failure to avoid dropping positions.
    """

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._last_prices: dict[str, Decimal] = {}

    async def _fetch_quote(self, symbol: str) -> Decimal | None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/quote",
                    params={"symbol": symbol, "token": self._api_key},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    price = data.get("c")
                    if price and price > 0:
                        return Decimal(str(price)).quantize(Decimal("0.01"))
        except Exception:
            logger.warning("failed to fetch quote from finnhub", symbol=symbol)
        return None

    async def fetch_prices(self, symbols: set[str]) -> dict[str, Decimal]:
        result = {}
        for symbol in symbols:
            price = await self._fetch_quote(symbol)

            if price:
                self._last_prices[symbol] = price
                result[symbol] = price
            elif symbol in self._last_prices:
                result[symbol] = self._last_prices[symbol]
            else:
                fallback = _FALLBACK_PRICES.get(symbol, _DEFAULT_FALLBACK)
                logger.warning("using fallback price", symbol=symbol, price=str(fallback))
                result[symbol] = fallback

        return result
