"""
Agent State Definition

TypedDict defining the state passed between agents in the LangGraph workflow.
This is the central data structure for the entire conversation flow.
"""

from typing import TypedDict, Optional, List, Annotated
from uuid import UUID
from datetime import datetime
from enum import Enum

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ConversationStage(str, Enum):
    """Stages in the loan conversation."""
    GREETING = "greeting"
    NEED_ANALYSIS = "need_analysis"
    COLLECTING_DETAILS = "collecting_details"
    KYC_VERIFICATION = "kyc_verification"
    OTP_VERIFICATION = "otp_verification"      # Verify PAN with OTP
    CREDIT_CHECK = "credit_check"
    SALARY_UPLOAD = "salary_upload"
    UNDERWRITING = "underwriting"
    DECISION = "decision"
    SCHEME_RECOMMENDATION = "scheme_recommendation"  # NEW: Compare schemes
    RATE_NEGOTIATION = "rate_negotiation"      # Negotiate interest rate
    SANCTION_LETTER = "sanction_letter"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"


class AgentType(str, Enum):
    """Agent types in the system."""
    MASTER = "master"
    SALES = "sales"
    VERIFICATION = "verification"
    UNDERWRITING = "underwriting"
    SCHEME = "scheme"              # NEW: Scheme comparison
    NEGOTIATION = "negotiation"
    SANCTION = "sanction"


class AgentState(TypedDict):
    """
    Central state object passed between all agents.
    
    Uses LangGraph's message annotation for automatic message handling.
    
    Attributes:
        messages: Conversation history with automatic merging
        conversation_id: Unique session identifier
        stage: Current conversation stage
        current_agent: Which agent is currently active
        
        # Customer Information
        customer_id: Customer UUID if identified
        customer_phone: Phone number for lookup
        customer_name: Customer's full name
        customer_pan: PAN card number
        customer_email: Email address
        
        # Application Data
        application_id: Loan application ID
        loan_amount: Requested loan amount
        tenure_months: Requested tenure
        loan_purpose: Purpose of loan
        
        # KYC Status
        kyc_verified: Whether KYC is complete
        kyc_data: Additional KYC information
        
        # Credit Data
        credit_score: CIBIL score
        pre_approved_limit: Pre-sanctioned limit
        credit_data: Full credit report data
        
        # Salary Verification
        salary_verified: Whether salary is verified
        monthly_salary: Verified monthly salary
        salary_slip_url: URL to uploaded salary slip
        
        # Underwriting Results
        decision: Final decision (APPROVED/REJECTED/MANUAL_REVIEW)
        decision_reason: Explanation for decision
        approved_amount: Final approved amount
        emi: Calculated EMI
        interest_rate: Applied interest rate
        risk_score: ML risk score
        risk_flags: List of risk indicators
        
        # Sanction
        sanction_id: Unique sanction letter ID
        sanction_letter_url: URL to sanction PDF
        
        # Error Handling
        error: Error message if any
        retry_count: Number of retries attempted
    """
    
    # LangGraph message handling
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Session tracking
    conversation_id: str
    stage: ConversationStage
    current_agent: Optional[AgentType]
    
    # Customer Information
    customer_id: Optional[str]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    customer_pan: Optional[str]
    customer_email: Optional[str]
    
    # Application Data
    application_id: Optional[str]
    loan_amount: Optional[int]
    tenure_months: Optional[int]
    loan_purpose: Optional[str]
    
    # KYC Status
    kyc_verified: bool
    kyc_data: Optional[dict]
    
    # OTP Verification (NEW)
    otp_code: Optional[str]        # Generated OTP for demo display
    otp_verified: bool             # Whether OTP was verified
    
    # Credit Data
    credit_score: Optional[int]
    pre_approved_limit: Optional[int]
    credit_data: Optional[dict]
    
    # Salary Verification
    salary_verified: bool
    monthly_salary: Optional[int]
    salary_slip_url: Optional[str]
    
    # Underwriting Results
    decision: Optional[str]
    decision_reason: Optional[str]
    approved_amount: Optional[int]
    emi: Optional[int]
    interest_rate: Optional[float]
    risk_score: Optional[float]
    risk_flags: Optional[List[str]]
    
    # Rate Negotiation
    rate_negotiation_attempts: int           # Number of negotiation attempts
    final_interest_rate: Optional[float]     # Rate after negotiation
    
    # Scheme Recommendations (NEW)
    scheme_recommendations: Optional[List[dict]]  # Top 3 scheme recommendations
    selected_scheme: Optional[dict]          # User's selected scheme
    
    # Sanction
    sanction_id: Optional[str]
    sanction_letter_url: Optional[str]
    
    # Error Handling
    error: Optional[str]
    retry_count: int
    
    # Timestamps
    updated_at: Optional[str]


def create_initial_state(conversation_id: str) -> AgentState:
    """
    Create a fresh agent state for a new conversation.
    
    Args:
        conversation_id: Unique conversation identifier.
    
    Returns:
        AgentState: Initialized state with defaults.
    """
    return AgentState(
        messages=[],
        conversation_id=conversation_id,
        stage=ConversationStage.GREETING,
        current_agent=AgentType.MASTER,
        
        # Customer
        customer_id=None,
        customer_phone=None,
        customer_name=None,
        customer_pan=None,
        customer_email=None,
        
        # Application
        application_id=None,
        loan_amount=None,
        tenure_months=None,
        loan_purpose=None,
        
        # KYC
        kyc_verified=False,
        kyc_data=None,
        
        # OTP Verification
        otp_code=None,
        otp_verified=False,
        
        # Credit
        credit_score=None,
        pre_approved_limit=None,
        credit_data=None,
        
        # Salary
        salary_verified=False,
        monthly_salary=None,
        salary_slip_url=None,
        
        # Underwriting
        decision=None,
        decision_reason=None,
        approved_amount=None,
        emi=None,
        interest_rate=None,
        risk_score=None,
        risk_flags=None,
        
        # Rate Negotiation
        rate_negotiation_attempts=0,
        final_interest_rate=None,
        
        # Scheme Recommendations
        scheme_recommendations=None,
        selected_scheme=None,
        
        # Sanction
        sanction_id=None,
        sanction_letter_url=None,
        
        # Error
        error=None,
        retry_count=0,
        
        # Timestamps
        updated_at=None,
    )
