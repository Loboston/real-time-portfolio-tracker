import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portfolio import Portfolio


async def get_by_id(session: AsyncSession, portfolio_id: uuid.UUID) -> Portfolio | None:
    result = await session.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id)
        .options(selectinload(Portfolio.positions))
    )
    return result.scalar_one_or_none()


async def get_all_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[Portfolio]:
    result = await session.execute(
        select(Portfolio)
        .where(Portfolio.user_id == user_id)
        .options(selectinload(Portfolio.positions))
        .order_by(Portfolio.created_at)
    )
    return list(result.scalars().all())


async def create(session: AsyncSession, user_id: uuid.UUID, name: str, description: str | None) -> Portfolio:
    portfolio = Portfolio(user_id=user_id, name=name, description=description)
    session.add(portfolio)
    await session.flush()
    return portfolio


async def delete(session: AsyncSession, portfolio: Portfolio) -> None:
    await session.delete(portfolio)
