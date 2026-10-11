from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.auth_schemas import LoginRequest, RegisterRequest


class AuthService:
    """Business logic for authentication operations."""

    async def register(self, db: AsyncSession, data: RegisterRequest) -> User:
        """
        Register a new user account.

        Raises:
            HTTPException 400 if email already exists
        """
        if await user_repository.email_exists(db, data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists",
            )

        user = await user_repository.create(
            db,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )
        return user

    async def login(self, db: AsyncSession, data: LoginRequest) -> tuple[User, str]:
        """
        Authenticate a user and return the user object with a JWT token.

        Returns:
            Tuple of (User, access_token)

        Raises:
            HTTPException 401 if credentials are invalid
            HTTPException 403 if account is inactive
        """
        user = await user_repository.get_by_email(db, data.email)

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated",
            )

        token = create_access_token(str(user.id), user.role)
        return user, token

    async def get_current_user_from_token(self, db: AsyncSession, user_id: str) -> User:
        """
        Look up and return the user associated with a decoded JWT token.

        Raises:
            HTTPException 401 if user not found or inactive
        """
        from uuid import UUID
        user = await user_repository.get_by_id(db, UUID(user_id))

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or account inactive",
            )

        return user


auth_service = AuthService()
