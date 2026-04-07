import asyncio
import json
from decimal import Decimal

import structlog

from app.cache.client import get_redis_client
from app.cache.price_cache import get_prices
from app.dependencies import async_session_factory
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

    # Find which subscribed portfolios hold this symbol
    affected = []
    async with async_session_factory() as session:
        for portfolio_id in subscribed_portfolio_ids:
            portfolio = await portfolio_repo.get_by_id(session, portfolio_id)
            if not portfolio:
                continue
            symbols_in_portfolio = {p.symbol for p in portfolio.positions}
            if symbol in symbols_in_portfolio:
                affected.append(portfolio)

    if not affected:
        return

    # Fetch all prices needed for affected portfolios in one pass
    all_symbols = {p.symbol for portfolio in affected for p in portfolio.positions}
    prices = await get_prices(all_symbols)

    for portfolio in affected:
        payload = _build_payload(portfolio, prices)
        await manager.broadcast_to_portfolio(portfolio.id, payload)


def _build_payload(portfolio, prices: dict[str, Decimal]) -> dict:
    positions = []
    total_value = Decimal("0")
    total_cost = Decimal("0")

    for position in portfolio.positions:
        current_price = prices.get(position.symbol)
        if current_price is None:
            continue

        market_value = position.quantity * current_price
        cost_basis = position.quantity * position.average_cost
        unrealized_pnl = market_value - cost_basis
        pnl_pct = (unrealized_pnl / cost_basis * 100).quantize(Decimal("0.01")) if cost_basis else Decimal("0")

        total_value += market_value
        total_cost += cost_basis

        positions.append({
            "symbol": position.symbol,
            "quantity": str(position.quantity),
            "average_cost": str(position.average_cost),
            "current_price": str(current_price),
            "market_value": str(market_value.quantize(Decimal("0.01"))),
            "unrealized_pnl": str(unrealized_pnl.quantize(Decimal("0.01"))),
            "pnl_pct": str(pnl_pct),
        })

    total_pnl = total_value - total_cost

    return {
        "portfolio_id": str(portfolio.id),
        "total_value": str(total_value.quantize(Decimal("0.01"))),
        "total_pnl": str(total_pnl.quantize(Decimal("0.01"))),
        "positions": positions,
    }
