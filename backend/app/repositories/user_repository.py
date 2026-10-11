from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access layer for User records. No business logic here."""

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.email == email.lower(), User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, **kwargs) -> User:
        if "email" in kwargs:
            kwargs["email"] = kwargs["email"].lower()
        user = User(**kwargs)
        db.add(user)
        await db.flush()  # Get the generated ID without committing
        await db.refresh(user)
        return user

    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        result = await db.execute(
            select(User.id).where(User.email == email.lower(), User.is_deleted == False)
        )
        return result.scalar_one_or_none() is not None


user_repository = UserRepository()
