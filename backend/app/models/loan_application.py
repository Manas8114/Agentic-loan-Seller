"""
Loan Application Model

Represents a loan application with status tracking, 
underwriting decision, and sanction details.
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum

from sqlalchemy import (
    String, Integer, DateTime, Text, Numeric,
    ForeignKey, Enum as SQLEnum, BigInteger
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.types import GUID, JSONB

from app.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer


class ApplicationStatus(str, Enum):
    """Loan application status enum."""
    INITIATED = "INITIATED"
    COLLECTING_INFO = "COLLECTING_INFO"
    KYC_PENDING = "KYC_PENDING"
    KYC_VERIFIED = "KYC_VERIFIED"
    KYC_FAILED = "KYC_FAILED"
    CREDIT_CHECK = "CREDIT_CHECK"
    SALARY_VERIFICATION = "SALARY_VERIFICATION"
    UNDERWRITING = "UNDERWRITING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SANCTIONED = "SANCTIONED"
    DISBURSED = "DISBURSED"
    CANCELLED = "CANCELLED"


class LoanApplication(Base):
    """
    Loan application model.
    
    Tracks the entire loan journey from initiation to disbursement.
    
    Attributes:
        id: Unique application identifier
        customer_id: Reference to customer
        requested_amount: Amount requested by customer
        approved_amount: Amount sanctioned (may differ)
        tenure_months: Loan tenure in months
        interest_rate: Annual interest rate percentage
        emi: Calculated EMI amount
        loan_purpose: Purpose of the loan
        status: Current application status
        decision_reason: Underwriting decision explanation
        ml_score: ML model probability score
        rule_engine_result: Rule engine evaluation details
        sanction_letter_url: S3 URL to sanction letter PDF
        conversation_id: Chat session identifier
        created_at: Application creation time
        updated_at: Last update time
    """
    
    __tablename__ = "loan_applications"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Application Reference Number (human-readable)
    application_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Customer Reference
    customer_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Loan Details
    requested_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    approved_amount: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    interest_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    emi: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    loan_purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Application Status
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus),
        default=ApplicationStatus.INITIATED,
        nullable=False,
        index=True
    )
    
    # Underwriting Results
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ml_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    rule_engine_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    risk_flags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Salary Verification
    salary_slip_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verified_salary: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Sanction Details
    sanction_letter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sanction_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sanctioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Conversation Tracking
    conversation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
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
    
    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="loan_applications",
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<LoanApplication(id={self.id}, status={self.status}, amount={self.requested_amount})>"
    
    @staticmethod
    def generate_application_number() -> str:
        """Generate unique application reference number."""
        import random
        import string
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.digits, k=6))
        return f"LA{timestamp}{random_suffix}"
