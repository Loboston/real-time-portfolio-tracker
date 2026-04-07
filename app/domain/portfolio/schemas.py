import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PortfolioCreate(BaseModel):
    name: str
    description: str | None = None


class PositionResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    quantity: Decimal
    average_cost: Decimal

    model_config = {"from_attributes": True}


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    positions: list[PositionResponse] = []

    model_config = {"from_attributes": True}
