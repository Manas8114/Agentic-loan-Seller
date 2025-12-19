"""
Audit Log Model

Immutable audit trail for all agent actions and system events.
Critical for compliance and debugging in BFSI applications.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.types import GUID, JSONB

from app.database import Base


class AuditLog(Base):
    """
    Audit log for tracking all system activities.
    
    Provides immutable trail of:
    - Agent actions and decisions
    - API requests and responses
    - State transitions
    - User interactions
    
    Attributes:
        id: Unique log entry identifier
        timestamp: When the action occurred
        action: Type of action performed
        agent_name: Which agent performed the action
        customer_id: Related customer (if applicable)
        application_id: Related loan application (if applicable)
        user_id: Admin/user who triggered action (if applicable)
        request_data: Sanitized request payload
        response_data: Sanitized response payload
        confidence_score: Agent confidence in decision
        duration_ms: Action execution time
        ip_address: Client IP (sanitized)
        user_agent: Client user agent
        status: Success/failure status
        error_message: Error details if failed
    """
    
    __tablename__ = "audit_logs"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Timestamp (immutable)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Action Details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Related Entities
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        nullable=True,
        index=True
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        nullable=True,
        index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        nullable=True,
        index=True
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    
    # Request/Response (PII sanitized)
    request_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    response_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Client Info (sanitized)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="SUCCESS",
        nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional Context
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, agent={self.agent_name})>"
