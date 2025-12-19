"""
Customer Schemas

Pydantic models for customer data validation and serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator
import re


class CustomerBase(BaseModel):
    """Base customer schema with common fields."""
    
    name: str = Field(..., min_length=2, max_length=255, description="Full name")
    phone: str = Field(..., pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile")
    email: Optional[EmailStr] = Field(None, description="Email address")
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name contains only valid characters."""
        if not re.match(r"^[a-zA-Z\s.'-]+$", v):
            raise ValueError("Name contains invalid characters")
        return v.strip().title()


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    
    pan: Optional[str] = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    aadhar_last_four: Optional[str] = Field(None, pattern=r"^\d{4}$")
    monthly_salary: Optional[int] = Field(None, ge=0)
    employer_name: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[str] = Field(None, pattern=r"^(SALARIED|SELF_EMPLOYED|BUSINESS)$")


class CustomerUpdate(BaseModel):
    """Schema for updating customer data."""
    
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    monthly_salary: Optional[int] = Field(None, ge=0)
    employer_name: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[str] = None


class CustomerResponse(BaseModel):
    """Schema for customer API responses."""
    
    id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    masked_pan: str = Field(..., description="Masked PAN (last 4 digits)")
    pre_approved_limit: int
    credit_score: Optional[int] = None
    kyc_verified: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class CustomerInDB(CustomerBase):
    """Full customer schema with all database fields."""
    
    id: UUID
    pan: Optional[str] = None
    aadhar_hash: Optional[str] = None
    pre_approved_limit: int = 0
    credit_score: Optional[int] = None
    monthly_salary: Optional[int] = None
    employer_name: Optional[str] = None
    employment_type: Optional[str] = None
    kyc_verified: bool = False
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class KYCVerifyRequest(BaseModel):
    """Request schema for KYC verification."""
    
    customer_id: UUID
    pan: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    aadhar_last_four: str = Field(..., pattern=r"^\d{4}$")


class KYCVerifyResponse(BaseModel):
    """Response schema for KYC verification."""
    
    customer_id: UUID
    verified: bool
    message: str
    pre_approved_limit: Optional[int] = None
    credit_score: Optional[int] = None
    kyc_verified_at: Optional[datetime] = None
