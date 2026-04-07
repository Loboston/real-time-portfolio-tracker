import json

import structlog

from app.cache.client import get_redis_client
from app.cache.price_cache import get_prices
from app.dependencies import async_session_factory
from app.domain.portfolio.calculator import compute_portfolio_metrics
from app.market_data.ingestor import PRICE_UPDATE_CHANNEL
from app.repositories import portfolio_repo
from app.websocket.manager import manager

logger = structlog.get_logger(__name__)


async def run_subscriber() -> None:
    """
    Listens to the Redis price_updates pub/sub channel.
    When a price changes, finds affected portfolios and broadcasts updated metrics.
    """
    logger.info("websocket subscriber started")

    redis = get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.subscribe(PRICE_UPDATE_CHANNEL)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            data = json.loads(message["data"])
            symbol = data["symbol"]
            await _handle_price_update(symbol)
        except Exception:
            logger.exception("subscriber failed to handle message", message=message)


async def _handle_price_update(symbol: str) -> None:
    subscribed_portfolio_ids = manager.get_subscribed_portfolio_ids()
    if not subscribed_portfolio_ids:
        return

    affected = []
    async with async_session_factory() as session:
        for portfolio_id in subscribed_portfolio_ids:
            portfolio = await portfolio_repo.get_by_id(session, portfolio_id)
            if not portfolio:
                continue
            if symbol in {p.symbol for p in portfolio.positions}:
                affected.append(portfolio)

    if not affected:
        return

    all_symbols = {p.symbol for portfolio in affected for p in portfolio.positions}
    prices = await get_prices(all_symbols)

    for portfolio in affected:
        payload = compute_portfolio_metrics(portfolio, prices)
        await manager.broadcast_to_portfolio(portfolio.id, payload)
