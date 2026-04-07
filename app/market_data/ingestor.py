import asyncio
import json

import structlog

from app.cache.client import get_redis_client
from app.cache.price_cache import get_price, set_price
from app.config import settings
from app.dependencies import async_session_factory
from app.market_data.base import MarketDataProvider
from app.repositories import position_repo

logger = structlog.get_logger(__name__)

PRICE_UPDATE_CHANNEL = "price_updates"


async def run_ingestor(provider: MarketDataProvider) -> None:
    """
    Background task that runs forever.
    Each tick: fetch prices → detect changes → cache → publish to Redis pub/sub.
    """
    logger.info("price ingestor started", interval=settings.price_poll_interval_seconds)

    while True:
        try:
            await _tick(provider)
        except Exception:
            logger.exception("ingestor tick failed — will retry next interval")

        await asyncio.sleep(settings.price_poll_interval_seconds)


async def _tick(provider: MarketDataProvider) -> None:
    # Get all symbols currently held across all portfolios
    async with async_session_factory() as session:
        symbols = await position_repo.get_all_symbols(session)

    if not symbols:
        return

    symbol_set = set(symbols)
    new_prices = await provider.fetch_prices(symbol_set)

    redis = get_redis_client()

    for symbol, new_price in new_prices.items():
        cached = await get_price(symbol)

        if cached == new_price:
            continue  # price unchanged — skip publish

        await set_price(symbol, new_price)

        message = json.dumps({"symbol": symbol, "price": str(new_price)})
        await redis.publish(PRICE_UPDATE_CHANNEL, message)

        logger.debug("price updated", symbol=symbol, price=str(new_price))
