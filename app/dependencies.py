import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token

engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — yields a transactional database session.
    Commits on clean exit, rolls back on exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user_id(authorization: str = Header(...)) -> uuid.UUID:
    """
    Extracts and validates the JWT from the Authorization header.
    Returns the user's UUID. Raises 401 if the token is missing or invalid.
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header")

    token = authorization.removeprefix("Bearer ")
    user_id = decode_access_token(token)

    if not user_id:
        raise UnauthorizedError("Invalid or expired token")

    return uuid.UUID(user_id)
