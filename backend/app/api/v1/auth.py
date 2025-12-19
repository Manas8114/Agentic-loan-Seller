"""
Authentication Routes

Handles user login, token refresh, and user management.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    Token,
    UserCreate,
    UserResponse,
    LoginRequest,
    RefreshTokenRequest,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.api.deps import CurrentUser, CurrentSuperuser, DBSession
from app.config import settings


router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    db: DBSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    OAuth2 compatible login endpoint.
    
    Returns JWT access and refresh tokens.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role.value
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: DBSession,
    request: RefreshTokenRequest
):
    """
    Refresh access token using refresh token.
    """
    payload = verify_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    from uuid import UUID
    user_id = UUID(payload.get("sub"))
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role.value
    )
    new_refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user info.
    """
    return current_user


@router.post("/register", response_model=UserResponse)
async def register_user(
    db: DBSession,
    user_in: UserCreate,
    current_user: CurrentSuperuser  # Only superusers can create users
):
    """
    Register a new user (admin only).
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/signup", response_model=UserResponse)
async def signup(
    db: DBSession,
    user_in: UserCreate
):
    """
    Public signup endpoint for new users.
    
    Creates a new user with VIEWER role.
    This endpoint is available in all environments.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with VIEWER role (non-admin)
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.VIEWER,  # Public signup gets VIEWER role
        is_active=True,
        is_superuser=False
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/init-admin", response_model=UserResponse)
async def initialize_admin(
    db: DBSession,
    user_in: UserCreate
):
    """
    Initialize the first admin user.
    
    Only works if no users exist in the database.
    This endpoint is DISABLED in production (when debug=False).
    """
    # Disable in production
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available"
        )
    
    # Check if any users exist
    result = await db.execute(select(User))
    existing = result.first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists"
        )
    
    # Create superuser
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user
