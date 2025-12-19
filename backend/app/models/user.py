"""
User Model

Admin and loan officer users for the system.
Separate from Customer model for security separation.
"""

import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types import GUID


class UserRole(str, Enum):
    """User role enum."""
    ADMIN = "ADMIN"
    LOAN_OFFICER = "LOAN_OFFICER"
    VIEWER = "VIEWER"


class User(Base):
    """
    System user model for admins and loan officers.
    
    Attributes:
        id: Unique identifier
        email: User email (login)
        hashed_password: Bcrypt hashed password
        full_name: Display name
        role: User role
        is_active: Account status
        is_superuser: Superadmin flag
        last_login: Last login timestamp
        created_at: Account creation time
        updated_at: Last update time
    """
    
    __tablename__ = "users"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Authorization
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.VIEWER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Activity Tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
