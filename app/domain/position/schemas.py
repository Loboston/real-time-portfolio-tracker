import uuid
from decimal import Decimal

from pydantic import BaseModel, field_validator


class PositionCreate(BaseModel):
    symbol: str
    quantity: Decimal
    average_cost: Decimal

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper()

    @field_validator("quantity", "average_cost")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("must be greater than zero")
        return v


class PositionUpdate(BaseModel):
    quantity: Decimal
    average_cost: Decimal

    @field_validator("quantity", "average_cost")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("must be greater than zero")
        return v


class PositionResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    symbol: str
    quantity: Decimal
    average_cost: Decimal

    model_config = {"from_attributes": True}
