import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position


async def get_by_id(session: AsyncSession, position_id: uuid.UUID) -> Position | None:
    result = await session.execute(select(Position).where(Position.id == position_id))
    return result.scalar_one_or_none()


async def get_by_portfolio_and_symbol(
    session: AsyncSession, portfolio_id: uuid.UUID, symbol: str
) -> Position | None:
    result = await session.execute(
        select(Position).where(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol.upper(),
        )
    )
    return result.scalar_one_or_none()


async def get_all_symbols(session: AsyncSession) -> list[str]:
    result = await session.execute(select(Position.symbol).distinct())
    return list(result.scalars().all())


async def create(
    session: AsyncSession,
    portfolio_id: uuid.UUID,
    symbol: str,
    quantity: Decimal,
    average_cost: Decimal,
) -> Position:
    position = Position(
        portfolio_id=portfolio_id,
        symbol=symbol.upper(),
        quantity=quantity,
        average_cost=average_cost,
    )
    session.add(position)
    await session.flush()
    return position


async def update(
    session: AsyncSession,
    position: Position,
    quantity: Decimal,
    average_cost: Decimal,
) -> Position:
    position.quantity = quantity
    position.average_cost = average_cost
    await session.flush()
    return position


async def delete(session: AsyncSession, position: Position) -> None:
    await session.delete(position)
