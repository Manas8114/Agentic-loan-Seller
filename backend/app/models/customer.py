"""
Customer Model

Represents a customer/applicant in the loan system.
Stores personal information, KYC data, and pre-approved limits.
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Text, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.loan_application import LoanApplication


class Customer(Base):
    """
    Customer model for loan applicants.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Full name of the customer
        phone: 10-digit mobile number
        email: Email address
        address: Full postal address
        pan: PAN card number (masked in logs)
        aadhar_hash: Hashed Aadhar number for privacy
        pre_approved_limit: Pre-sanctioned loan limit
        credit_score: CIBIL score (300-900)
        monthly_salary: Monthly income in INR
        employer_name: Current employer
        employment_type: Employment category
        date_of_birth: Customer's DOB
        kyc_verified: Whether KYC is complete
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "customers"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Personal Information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # KYC Information
    pan: Mapped[Optional[str]] = mapped_column(String(10), unique=True, nullable=True)
    aadhar_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Financial Information
    pre_approved_limit: Mapped[int] = mapped_column(BigInteger, default=0)
    credit_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    monthly_salary: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Employment Information
    employer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employment_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
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
    loan_applications: Mapped[List["LoanApplication"]] = relationship(
        "LoanApplication",
        back_populates="customer",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name={self.name}, phone={self.phone})>"
    
    @property
    def masked_pan(self) -> str:
        """Return PAN with first 6 characters masked."""
        if self.pan and len(self.pan) == 10:
            return f"XXXXXX{self.pan[-4:]}"
        return "XXXXXXXXXX"
    
    @property
    def masked_aadhar(self) -> str:
        """Return masked Aadhar representation."""
        return "XXXX-XXXX-XXXX"
