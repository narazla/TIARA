from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.security import (
    decode_token,
    oauth2_scheme,
    verify_caregiver_dashboard_token,
)
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
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
        )
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
        )

    from uuid import UUID
    user = await user_repository.get_by_id(db, UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan atau akun tidak aktif",
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
        peran = str(getattr(current_user.role, "value", current_user.role))
        if peran not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke fitur ini",
            )
        return current_user
    return _check_role


async def require_caregiver_pin(
    current_user: User = Depends(require_role(Role.CAREGIVER)),
    x_dashboard_token: Optional[str] = Header(default=None),
) -> User:
    """
    Wajibkan caregiver membawa token dashboard (hasil verifikasi PIN) milik akunnya sendiri.
    Bila token tidak ada, habis, atau milik akun lain, jawab 403 PIN_DIPERLUKAN
    agar frontend mengarahkan pengguna ke halaman PIN.
    """
    harus_pin = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="PIN_DIPERLUKAN",
    )
    if not x_dashboard_token:
        raise harus_pin
    try:
        pemilik = verify_caregiver_dashboard_token(x_dashboard_token)
    except HTTPException:
        raise harus_pin
    if str(pemilik) != str(current_user.id):
        raise harus_pin
    return current_user
