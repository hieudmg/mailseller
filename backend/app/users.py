import os
import uuid
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    Strategy, CookieTransport,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserToken, get_user_db, get_async_session
from app.core.token_utils import generate_user_token
from app.core.memory_manager import memory_manager

SECRET = os.getenv('AUTH_SECRET')


class MemoryStrategy(Strategy[models.UP, models.ID]):
    """Authentication strategy using in-memory session storage."""

    def __init__(self, lifetime_seconds: int = 3600):
        self.lifetime_seconds = lifetime_seconds

    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[models.UP, models.ID]
    ) -> Optional[models.UP]:
        """Read user from session token."""
        if token is None:
            return None

        user_id = memory_manager.get_session(token)
        if user_id is None:
            return None

        try:
            user = await user_manager.get(user_id)
            return user
        except Exception:
            return None

    async def write_token(self, user: models.UP) -> str:
        """Create session token for user."""
        token = generate_user_token(str(user.id))
        memory_manager.create_session(token, user.id, self.lifetime_seconds)
        return token

    async def destroy_token(self, token: str, user: models.UP) -> None:
        """Destroy session token."""
        memory_manager.delete_session(token)


class UserManager(BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    def parse_id(self, value: str) -> int:
        return int(value)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

        # Generate API token
        token = generate_user_token(user.email)

        # Save token to database
        async for session in get_async_session():
            user_token = UserToken(user_id=user.id, token=token)
            session.add(user_token)
            await session.commit()

            # Store token in memory for fast authentication
            memory_manager.set_user_token(user.id, token)

            print(f"Generated API token for user {user.id}: {token}")
            break

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
cookie_transport = CookieTransport(cookie_max_age=3600)


def get_auth_strategy() -> Strategy[models.UP, models.ID]:
    return MemoryStrategy(lifetime_seconds=3600)


web_auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_auth_strategy,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [web_auth_backend])

current_active_user = fastapi_users.current_user(active=True)


# Token authentication dependency for API-only endpoints
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Authenticate user by bearer token from user_token table."""
    from fastapi import HTTPException
    from sqlalchemy import select

    token = credentials.credentials

    # First check memory for fast authentication
    user_id = memory_manager.get_user_id_by_token(token)

    if user_id is None:
        # Fallback to database if not in memory
        result = await session.execute(
            select(UserToken).where(UserToken.token == token)
        )
        user_token = result.scalar_one_or_none()

        if user_token is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        user_id = user_token.user_id

        # Cache token in memory for future requests
        memory_manager.set_user_token(user_id, token)

    # Get user from database
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive user")

    return user
