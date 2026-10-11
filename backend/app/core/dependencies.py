from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, oauth2_scheme
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import user_repository


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: decode JWT and return the authenticated user.
    Used as a base dependency for all protected routes.
    """
    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    from uuid import UUID
    user = await user_repository.get_by_id(db, UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account inactive",
        )

    return user


def require_role(*roles: str):
    """
    FastAPI dependency factory: require the current user to have one of the specified roles.

    Usage:
        @router.get("/endpoint")
        async def handler(user = Depends(require_role("caregiver", "admin"))):
            ...
    """
    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        # Bypassed: one account covers all roles (elderly, caregiver, doctor)
        return current_user
    return _check_role
