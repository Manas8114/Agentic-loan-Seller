"""
Chat Schemas

Pydantic models for chat API and conversation state.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentType(str, Enum):
    """Agent types in the system."""
    MASTER = "master"
    SALES = "sales"
    VERIFICATION = "verification"
    UNDERWRITING = "underwriting"
    SCHEME = "scheme"
    NEGOTIATION = "negotiation"
    SANCTION = "sanction"


class ConversationStage(str, Enum):
    """Stages in the loan conversation."""
    GREETING = "greeting"
    NEED_ANALYSIS = "need_analysis"
    COLLECTING_DETAILS = "collecting_details"
    KYC_VERIFICATION = "kyc_verification"
    OTP_VERIFICATION = "otp_verification"
    CREDIT_CHECK = "credit_check"
    SALARY_UPLOAD = "salary_upload"
    UNDERWRITING = "underwriting"
    DECISION = "decision"
    SCHEME_RECOMMENDATION = "scheme_recommendation"
    RATE_NEGOTIATION = "rate_negotiation"
    SANCTION_LETTER = "sanction_letter"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"


class ChatMessage(BaseModel):
    """Individual chat message."""
    
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_type: Optional[AgentType] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    customer_phone: Optional[str] = Field(None, pattern=r"^[6-9]\d{9}$")
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    
    conversation_id: str
    message: str
    agent_type: AgentType
    stage: ConversationStage
    actions: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    application_id: Optional[str] = None  # Changed from UUID to str to support LOAN-YYYYMMDD-XXXXXXXX format
    requires_input: Optional[str] = None  # e.g., "pan", "salary_slip", "confirm"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    """Full conversation state for LangGraph."""
    
    conversation_id: str
    stage: ConversationStage = ConversationStage.GREETING
    messages: List[ChatMessage] = []
    
    # Customer Information
    customer_id: Optional[UUID] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    
    # Loan Request
    application_id: Optional[str] = None  # Changed from UUID to support LOAN-YYYYMMDD-XXXXXXXX format
    loan_amount: Optional[int] = None
    tenure_months: Optional[int] = None
    loan_purpose: Optional[str] = None
    
    # KYC Data
    kyc_verified: bool = False
    pan: Optional[str] = None
    
    # Credit Data
    credit_score: Optional[int] = None
    pre_approved_limit: Optional[int] = None
    
    # Salary Data
    salary_verified: bool = False
    monthly_salary: Optional[int] = None
    salary_slip_url: Optional[str] = None
    
    # Decision
    decision: Optional[str] = None  # APPROVED, REJECTED, MANUAL_REVIEW
    decision_reason: Optional[str] = None
    approved_amount: Optional[int] = None
    emi: Optional[int] = None
    interest_rate: Optional[float] = None
    
    # Sanction
    sanction_letter_url: Optional[str] = None
    
    # Tracking
    current_agent: Optional[AgentType] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Summary of a conversation."""
    
    conversation_id: str
    customer_name: Optional[str] = None
    stage: ConversationStage
    status: Optional[str] = None
    loan_amount: Optional[int] = None
    decision: Optional[str] = None
    message_count: int
    created_at: datetime
    updated_at: datetime
