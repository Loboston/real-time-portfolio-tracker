import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.domain.position import service
from app.domain.position.schemas import PositionCreate, PositionResponse, PositionUpdate

router = APIRouter(prefix="/portfolios/{portfolio_id}/positions", tags=["positions"])


@router.post("", response_model=PositionResponse, status_code=201)
async def add_position(
    portfolio_id: uuid.UUID,
    data: PositionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    return await service.add_position(session, user_id, portfolio_id, data)


@router.put("/{position_id}", response_model=PositionResponse)
async def update_position(
    portfolio_id: uuid.UUID,
    position_id: uuid.UUID,
    data: PositionUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    return await service.update_position(session, user_id, portfolio_id, position_id, data)


@router.delete("/{position_id}", status_code=204)
async def delete_position(
    portfolio_id: uuid.UUID,
    position_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    await service.delete_position(session, user_id, portfolio_id, position_id)
