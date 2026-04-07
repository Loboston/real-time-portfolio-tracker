import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    email: str,
    hashed_password: str,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email.lower(),
        hashed_password=hashed_password,
        display_name=display_name,
    )
    session.add(user)
    await session.flush()  # writes to DB within the transaction and assigns the generated id
    return user
