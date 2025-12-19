"""
API v1 Router

Aggregates all v1 API routes.
"""

from fastapi import APIRouter

from app.api.v1 import auth, chat, kyc, credit, underwrite, sanction, applications


api_router = APIRouter(prefix="/api/v1")

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(kyc.router, prefix="/kyc", tags=["KYC Verification"])
api_router.include_router(credit.router, prefix="/credit", tags=["Credit Bureau"])
api_router.include_router(underwrite.router, prefix="/underwrite", tags=["Underwriting"])
api_router.include_router(sanction.router, prefix="/sanction", tags=["Sanction Letter"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
