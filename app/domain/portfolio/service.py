import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.domain.portfolio.schemas import PortfolioCreate, PortfolioResponse
from app.repositories import portfolio_repo


async def create_portfolio(
    session: AsyncSession, user_id: uuid.UUID, data: PortfolioCreate
) -> PortfolioResponse:
    existing = await portfolio_repo.get_all_for_user(session, user_id)
    if any(p.name.lower() == data.name.lower() for p in existing):
        raise ConflictError(f"A portfolio named '{data.name}' already exists")

    portfolio = await portfolio_repo.create(session, user_id, data.name, data.description)
    return PortfolioResponse.model_validate(portfolio)


async def get_portfolio(
    session: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> PortfolioResponse:
    portfolio = await portfolio_repo.get_by_id(session, portfolio_id)

    if not portfolio:
        raise NotFoundError("Portfolio not found")
    if portfolio.user_id != user_id:
        raise ForbiddenError()

    return PortfolioResponse.model_validate(portfolio)


async def list_portfolios(session: AsyncSession, user_id: uuid.UUID) -> list[PortfolioResponse]:
    portfolios = await portfolio_repo.get_all_for_user(session, user_id)
    return [PortfolioResponse.model_validate(p) for p in portfolios]


async def delete_portfolio(
    session: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> None:
    portfolio = await portfolio_repo.get_by_id(session, portfolio_id)

    if not portfolio:
        raise NotFoundError("Portfolio not found")
    if portfolio.user_id != user_id:
        raise ForbiddenError()

    await portfolio_repo.delete(session, portfolio)
