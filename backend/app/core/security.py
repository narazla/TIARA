from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# Password hashing context — bcrypt with 12 rounds
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_pin(pin: str) -> str:
    """Hash a caregiver PIN using bcrypt."""
    return pwd_context.hash(pin)


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify a plain PIN against its bcrypt hash."""
    return pwd_context.verify(plain_pin, hashed_pin)


def create_access_token(user_id: str, role: str, extra_claims: Optional[dict] = None) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: The user's UUID as string
        role: User role (elderly, caregiver, healthcare, admin)
        extra_claims: Optional additional payload fields

    Returns:
        Signed JWT string
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_caregiver_dashboard_token(caregiver_user_id: str) -> str:
    """
    Create a short-lived token granting caregiver dashboard access after PIN verification.

    This is separate from the main access token to require PIN re-entry
    when the session expires or on a new device access.
    """
    expire = datetime.utcnow() + timedelta(
        minutes=settings.CAREGIVER_DASHBOARD_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": caregiver_user_id,
        "scope": "caregiver_dashboard",
        "exp": expire,
        "type": "dashboard",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises:
        HTTPException 401 if token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_caregiver_dashboard_token(token: str) -> str:
    """
    Verify a caregiver dashboard token and return the caregiver_user_id.

    Raises:
        HTTPException 401 if token is invalid, expired, or wrong scope
    """
    payload = decode_token(token)
    if payload.get("scope") != "caregiver_dashboard":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dashboard token",
        )
    return payload["sub"]
