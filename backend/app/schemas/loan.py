"""
Loan Application Schemas

Pydantic models for loan applications and underwriting.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class ApplicationStatusEnum(str, Enum):
    """Loan application status."""
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


class LoanApplicationCreate(BaseModel):
    """Schema for creating a loan application."""
    
    customer_id: UUID
    requested_amount: int = Field(..., gt=0, le=10000000, description="Amount in INR")
    tenure_months: int = Field(..., ge=6, le=84, description="Tenure in months")
    loan_purpose: Optional[str] = Field(None, max_length=255)
    conversation_id: Optional[str] = None


class LoanApplicationUpdate(BaseModel):
    """Schema for updating a loan application."""
    
    requested_amount: Optional[int] = Field(None, gt=0, le=10000000)
    tenure_months: Optional[int] = Field(None, ge=6, le=84)
    loan_purpose: Optional[str] = Field(None, max_length=255)
    status: Optional[ApplicationStatusEnum] = None


class LoanApplicationResponse(BaseModel):
    """Schema for loan application API responses."""
    
    id: UUID
    application_number: str
    customer_id: UUID
    customer_name: Optional[str] = None
    requested_amount: int
    approved_amount: Optional[int] = None
    tenure_months: int
    interest_rate: Optional[float] = None
    emi: Optional[int] = None
    loan_purpose: Optional[str] = None
    status: ApplicationStatusEnum
    decision_reason: Optional[str] = None
    sanction_letter_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class RuleEngineResult(BaseModel):
    """Result from rule-based underwriting."""
    
    rule_name: str
    passed: bool
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None


class UnderwritingRequest(BaseModel):
    """Request schema for underwriting decision."""
    
    application_id: UUID
    customer_id: UUID
    requested_amount: int
    tenure_months: int
    credit_score: int
    monthly_salary: int
    pre_approved_limit: int
    existing_emi: Optional[int] = 0
    

class UnderwritingResponse(BaseModel):
    """Response schema for underwriting decision."""
    
    application_id: UUID
    decision: str = Field(..., pattern=r"^(APPROVED|REJECTED|MANUAL_REVIEW)$")
    approved_amount: Optional[int] = None
    interest_rate: Optional[float] = None
    emi: Optional[int] = None
    risk_score: Optional[float] = None
    ml_probability: Optional[float] = None
    rules_result: List[RuleEngineResult] = []
    risk_flags: List[str] = []
    decision_reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class SanctionLetterRequest(BaseModel):
    """Request to generate sanction letter."""
    
    application_id: UUID


class SanctionLetterResponse(BaseModel):
    """Response with sanction letter download URL."""
    
    application_id: UUID
    sanction_id: str
    download_url: str
    generated_at: datetime


class CreditScoreRequest(BaseModel):
    """Request for credit score lookup."""
    
    customer_id: UUID
    pan: str


class CreditScoreResponse(BaseModel):
    """Mock credit bureau response."""
    
    customer_id: UUID
    credit_score: int = Field(..., ge=300, le=900)
    score_date: datetime
    active_accounts: int
    total_outstanding: int
    delinquent_accounts: int
    credit_utilization: float
    payment_history_score: int


class EMICalculationRequest(BaseModel):
    """Request for EMI calculation."""
    
    principal: int = Field(..., gt=0)
    annual_rate: float = Field(..., gt=0, le=50)
    tenure_months: int = Field(..., ge=1, le=360)


class EMICalculationResponse(BaseModel):
    """EMI calculation result."""
    
    principal: int
    annual_rate: float
    tenure_months: int
    emi: int
    total_payment: int
    total_interest: int
