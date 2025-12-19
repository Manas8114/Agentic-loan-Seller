"""
Underwriting Routes

Loan underwriting decision endpoint using rule engine + ML scoring.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form

from app.schemas.loan import (
    UnderwritingRequest,
    UnderwritingResponse,
    EMICalculationRequest,
    EMICalculationResponse,
)
from app.api.deps import DBSession
from app.services.underwriting_engine import UnderwritingEngine
from app.services.ocr_service import OCRService
from app.core.logging import get_logger


router = APIRouter()
logger = get_logger(__name__)


@router.post("/decide", response_model=UnderwritingResponse)
async def underwrite_application(
    request: UnderwritingRequest,
    db: DBSession
):
    """
    Make underwriting decision for a loan application.
    
    Process:
    1. Validate input parameters
    2. Run rule-based checks
    3. Calculate EMI and debt ratios
    4. Run ML model for risk scoring
    5. Combine results for final decision
    
    Rules:
    - Credit score >= 700 required
    - EMI <= 50% of salary
    - Loan <= 2x pre-approved limit (with salary verification)
    """
    logger.info(
        "Underwriting request",
        application_id=str(request.application_id),
        amount=request.requested_amount
    )
    
    engine = UnderwritingEngine(db)
    
    try:
        result = await engine.evaluate(request)
        
        logger.info(
            "Underwriting decision",
            application_id=str(request.application_id),
            decision=result.decision,
            confidence=result.confidence
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Underwriting error",
            application_id=str(request.application_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Underwriting process failed"
        )


@router.post("/calculate-emi", response_model=EMICalculationResponse)
async def calculate_emi(
    request: EMICalculationRequest
):
    """
    Calculate EMI for given loan parameters.
    
    Formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    Where:
        P = Principal amount
        r = Monthly interest rate (annual_rate / 12 / 100)
        n = Tenure in months
    """
    principal = request.principal
    annual_rate = request.annual_rate
    tenure = request.tenure_months
    
    # Calculate monthly rate
    monthly_rate = annual_rate / 12 / 100
    
    # EMI calculation
    if monthly_rate > 0:
        emi_factor = (1 + monthly_rate) ** tenure
        emi = int(principal * monthly_rate * emi_factor / (emi_factor - 1))
    else:
        emi = int(principal / tenure)
    
    total_payment = emi * tenure
    total_interest = total_payment - principal
    
    return EMICalculationResponse(
        principal=principal,
        annual_rate=annual_rate,
        tenure_months=tenure,
        emi=emi,
        total_payment=total_payment,
        total_interest=total_interest
    )


@router.post("/upload-salary")
async def upload_salary_slip(
    application_id: UUID = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload and process salary slip for verification.
    
    Accepts PDF or image files.
    Uses OCR to extract salary information.
    """
    logger.info(
        "Salary slip upload",
        application_id=str(application_id),
        filename=file.filename,
        content_type=file.content_type
    )
    
    # Validate file type
    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: PDF, JPEG, PNG"
        )
    
    # Read file content
    content = await file.read()
    
    # Process with OCR
    ocr_service = OCRService()
    
    try:
        extracted_data = await ocr_service.extract_salary_info(
            content=content,
            content_type=file.content_type,
            filename=file.filename
        )
        
        logger.info(
            "Salary extracted",
            application_id=str(application_id),
            gross_salary=extracted_data.get("gross_salary"),
            net_salary=extracted_data.get("net_salary")
        )
        
        return {
            "success": True,
            "application_id": str(application_id),
            "extracted_data": extracted_data,
            "file_url": f"/uploads/salary/{application_id}/{file.filename}"
        }
        
    except Exception as e:
        logger.error(
            "OCR processing failed",
            application_id=str(application_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract salary information from document"
        )


@router.get("/risk-flags/{application_id}")
async def get_risk_flags(
    application_id: UUID,
    db: DBSession
):
    """
    Get risk flags for an application.
    
    Returns list of risk indicators identified during underwriting.
    """
    engine = UnderwritingEngine(db)
    
    flags = await engine.get_risk_flags(application_id)
    
    return {
        "application_id": str(application_id),
        "risk_flags": flags
    }
