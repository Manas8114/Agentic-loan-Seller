"""
Credit Bureau Routes

Mock credit bureau API for fetching credit scores.
Simulates CIBIL-style credit data.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.loan import CreditScoreResponse
from app.api.deps import DBSession
from app.services.credit_service import CreditService
from app.core.logging import get_logger


router = APIRouter()
logger = get_logger(__name__)


@router.get("/score/{customer_id}", response_model=CreditScoreResponse)
async def get_credit_score(
    customer_id: UUID,
    db: DBSession
):
    """
    Fetch credit score for a customer.
    
    Returns CIBIL-style credit data including:
    - Credit score (300-900)
    - Active accounts
    - Total outstanding
    - Delinquency history
    - Credit utilization
    """
    logger.info(
        "Credit score request",
        customer_id=str(customer_id)
    )
    
    credit_service = CreditService(db)
    
    try:
        result = await credit_service.get_credit_report(customer_id)
        
        logger.info(
            "Credit score fetched",
            customer_id=str(customer_id),
            score=result.credit_score
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/score-by-pan/{pan}")
async def get_credit_score_by_pan(
    pan: str,
    db: DBSession
):
    """
    Fetch credit score using PAN number.
    
    Alternative lookup method when customer_id is not known.
    """
    credit_service = CreditService(db)
    
    customer = await credit_service.find_customer_by_pan(pan)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found with given PAN"
        )
    
    result = await credit_service.get_credit_report(customer.id)
    return result


@router.post("/refresh/{customer_id}")
async def refresh_credit_score(
    customer_id: UUID,
    db: DBSession
):
    """
    Refresh credit score from bureau.
    
    In production, this would make an actual bureau call.
    Here it simulates fetching fresh data.
    """
    credit_service = CreditService(db)
    
    try:
        result = await credit_service.refresh_credit_score(customer_id)
        
        return {
            "message": "Credit score refreshed",
            "customer_id": str(customer_id),
            "new_score": result.credit_score,
            "refreshed_at": result.score_date.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
