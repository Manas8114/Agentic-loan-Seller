"""
Pydantic Schemas Package

Contains all request/response schemas for API validation.
"""

from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerInDB,
)
from app.schemas.loan import (
    LoanApplicationCreate,
    LoanApplicationUpdate,
    LoanApplicationResponse,
    UnderwritingRequest,
    UnderwritingResponse,
)
from app.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationState,
)
from app.schemas.auth import (
    Token,
    TokenPayload,
    UserCreate,
    UserResponse,
    LoginRequest,
)


__all__ = [
    # Customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerInDB",
    # Loan
    "LoanApplicationCreate",
    "LoanApplicationUpdate",
    "LoanApplicationResponse",
    "UnderwritingRequest",
    "UnderwritingResponse",
    # Chat
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ConversationState",
    # Auth
    "Token",
    "TokenPayload",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
]
