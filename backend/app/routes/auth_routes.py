from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.
    Email must be unique. Password is hashed with bcrypt before storage.
    """
    user = await auth_service.register(db, data)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate with email and password.
    Returns a JWT access token and the user's profile.
    """
    user, token = await auth_service.login(db, data)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    Requires a valid JWT token in the Authorization header.
    """
    return current_user


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Log out the current user.
    Token invalidation is handled client-side (remove token from storage).
    Post-MVP: add server-side token blacklist for full invalidation.
    """
    return MessageResponse(message="Logged out successfully")
