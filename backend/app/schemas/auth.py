"""
Authentication Schemas

Pydantic models for JWT authentication and user management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, model_validator


class UserRole(str, Enum):
    """User role enum."""
    ADMIN = "ADMIN"
    LOAN_OFFICER = "LOAN_OFFICER"
    VIEWER = "VIEWER"


class Token(BaseModel):
    """JWT token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")


class TokenPayload(BaseModel):
    """JWT token payload."""
    
    sub: str  # User ID
    email: str
    role: UserRole
    exp: datetime
    iat: datetime


class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    """Schema for updating user data."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user API responses."""
    
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    """Schema for password change."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    
    refresh_token: str
