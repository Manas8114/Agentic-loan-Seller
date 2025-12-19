"""
KYC Verification Routes

Handles customer KYC verification against mock CRM data.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.customer import KYCVerifyRequest, KYCVerifyResponse
from app.api.deps import DBSession
from app.services.kyc_service import KYCService
from app.core.logging import get_logger


router = APIRouter()
logger = get_logger(__name__)


@router.post("/verify", response_model=KYCVerifyResponse)
async def verify_kyc(
    request: KYCVerifyRequest,
    db: DBSession
):
    """
    Verify customer KYC details against CRM database.
    
    Validates:
    - PAN card number format and existence
    - Aadhar last 4 digits match
    - Customer exists in system
    
    Returns pre-approved limit and credit score if verified.
    """
    logger.info(
        "KYC verification request",
        customer_id=str(request.customer_id)
    )
    
    kyc_service = KYCService(db)
    
    try:
        result = await kyc_service.verify_customer(
            customer_id=request.customer_id,
            pan=request.pan,
            aadhar_last_four=request.aadhar_last_four
        )
        
        logger.info(
            "KYC verification result",
            customer_id=str(request.customer_id),
            verified=result.verified
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/status/{customer_id}")
async def get_kyc_status(
    customer_id: UUID,
    db: DBSession
):
    """
    Get KYC verification status for a customer.
    """
    kyc_service = KYCService(db)
    
    status_result = await kyc_service.get_status(customer_id)
    
    if not status_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return status_result


@router.post("/lookup-by-phone")
async def lookup_customer_by_phone(
    request: dict,
    db: DBSession
):
    """
    Look up customer by phone number.
    
    Used during chat to identify existing customers.
    """
    phone = request.get("phone", "")
    
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    kyc_service = KYCService(db)
    
    customer = await kyc_service.find_by_phone(phone)
    
    if not customer:
        return {
            "found": False,
            "message": "Customer not found. Please provide your details."
        }
    
    return {
        "found": True,
        "customer_id": str(customer.id),
        "name": customer.name,
        "kyc_verified": customer.kyc_verified,
        "pre_approved_limit": customer.pre_approved_limit
    }
