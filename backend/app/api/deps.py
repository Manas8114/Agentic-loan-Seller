"""
API Dependencies

Shared dependencies for FastAPI routes including
authentication, database sessions, and rate limiting.
"""

from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole
from app.schemas.auth import TokenPayload


# OAuth2 scheme for JWT tokens
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[Optional[str], Depends(oauth2_scheme)]
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    
    Returns None if no token or invalid token.
    Use get_current_user_required for endpoints that require auth.
    """
    if not token:
        return None
    
    payload = verify_token(token, token_type="access")
    if not payload:
        return None
    
    try:
        user_id = UUID(payload.get("sub"))
    except (ValueError, TypeError):
        return None
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    return user


async def get_current_user_required(
    user: Annotated[Optional[User], Depends(get_current_user)]
) -> User:
    """
    Get current user, raising exception if not authenticated.
    
    Use this for protected endpoints.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin_user(
    user: Annotated[User, Depends(get_current_user_required)]
) -> User:
    """
    Get current user, requiring ADMIN or LOAN_OFFICER role.
    """
    if user.role not in [UserRole.ADMIN, UserRole.LOAN_OFFICER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return user


async def get_current_superuser(
    user: Annotated[User, Depends(get_current_user_required)]
) -> User:
    """
    Get current user, requiring superuser status.
    """
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return user


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for proxy headers first
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    if request.client:
        return request.client.host
    
    return "unknown"


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user_required)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
