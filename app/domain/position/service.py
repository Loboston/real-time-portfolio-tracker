import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.domain.position.schemas import PositionCreate, PositionResponse, PositionUpdate
from app.repositories import portfolio_repo, position_repo


async def _get_portfolio_or_raise(session: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID):
    portfolio = await portfolio_repo.get_by_id(session, portfolio_id)
    if not portfolio:
        raise NotFoundError("Portfolio not found")
    if portfolio.user_id != user_id:
        raise ForbiddenError()
    return portfolio


async def add_position(
    session: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID, data: PositionCreate
) -> PositionResponse:
    await _get_portfolio_or_raise(session, user_id, portfolio_id)

    existing = await position_repo.get_by_portfolio_and_symbol(session, portfolio_id, data.symbol)
    if existing:
        raise ConflictError(f"A position for {data.symbol} already exists in this portfolio")

    position = await position_repo.create(
        session, portfolio_id, data.symbol, data.quantity, data.average_cost
    )
    return PositionResponse.model_validate(position)


async def update_position(
    session: AsyncSession,
    user_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    position_id: uuid.UUID,
    data: PositionUpdate,
) -> PositionResponse:
    await _get_portfolio_or_raise(session, user_id, portfolio_id)

    position = await position_repo.get_by_id(session, position_id)
    if not position or position.portfolio_id != portfolio_id:
        raise NotFoundError("Position not found")

    position = await position_repo.update(session, position, data.quantity, data.average_cost)
    return PositionResponse.model_validate(position)


async def delete_position(
    session: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID, position_id: uuid.UUID
) -> None:
    await _get_portfolio_or_raise(session, user_id, portfolio_id)

    position = await position_repo.get_by_id(session, position_id)
    if not position or position.portfolio_id != portfolio_id:
        raise NotFoundError("Position not found")

    await position_repo.delete(session, position)
