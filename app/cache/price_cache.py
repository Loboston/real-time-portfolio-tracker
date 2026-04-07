import json
from decimal import Decimal

from app.cache.client import get_redis_client

_PRICE_KEY_PREFIX = "price:"
_PRICE_TTL_SECONDS = 60  # prices expire after 60 seconds if ingestor stops


def _key(symbol: str) -> str:
    return f"{_PRICE_KEY_PREFIX}{symbol.upper()}"


async def set_price(symbol: str, price: Decimal) -> None:
    redis = get_redis_client()
    await redis.setex(_key(symbol), _PRICE_TTL_SECONDS, str(price))


async def get_price(symbol: str) -> Decimal | None:
    redis = get_redis_client()
    value = await redis.get(_key(symbol))
    if value is None:
        return None
    return Decimal(value)


async def get_prices(symbols: set[str]) -> dict[str, Decimal]:
    """Fetch multiple prices in one round trip using a pipeline."""
    if not symbols:
        return {}

    redis = get_redis_client()
    keys = [_key(s) for s in symbols]

    async with redis.pipeline() as pipe:
        for key in keys:
            pipe.get(key)
        values = await pipe.execute()

    result = {}
    for symbol, value in zip(symbols, values):
        if value is not None:
            result[symbol] = Decimal(value)
    return result
