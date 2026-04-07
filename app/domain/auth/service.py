from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.repositories import user_repo


async def register(session: AsyncSession, data: RegisterRequest) -> TokenResponse:
    existing = await user_repo.get_by_email(session, data.email)
    if existing:
        raise ConflictError("An account with that email already exists")

    user = await user_repo.create(
        session,
        email=data.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name,
    )

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


async def login(session: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = await user_repo.get_by_email(session, data.email)

    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)
