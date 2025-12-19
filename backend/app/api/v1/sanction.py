"""
Sanction Letter Routes

Generate and serve loan sanction letter PDFs.
"""

from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.loan import SanctionLetterRequest, SanctionLetterResponse
from app.api.deps import DBSession
from app.services.pdf_generator import SanctionLetterGenerator
from app.core.logging import get_logger


router = APIRouter()
logger = get_logger(__name__)


@router.post("/generate", response_model=SanctionLetterResponse)
async def generate_sanction_letter(
    request: SanctionLetterRequest,
    db: DBSession
):
    """
    Generate sanction letter PDF for an approved application.
    
    The sanction letter includes:
    - Customer details (name, address, PAN masked)
    - Loan details (amount, tenure, interest rate, EMI)
    - Unique sanction ID
    - Terms and conditions
    - Digital signature block
    """
    logger.info(
        "Sanction letter generation request",
        application_id=str(request.application_id)
    )
    
    generator = SanctionLetterGenerator(db)
    
    try:
        result = await generator.generate(request.application_id)
        
        logger.info(
            "Sanction letter generated",
            application_id=str(request.application_id),
            sanction_id=result.sanction_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Sanction letter generation failed",
            application_id=str(request.application_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate sanction letter"
        )


@router.get("/download/{application_id}")
async def download_sanction_letter(
    application_id: UUID,
    db: DBSession
):
    """
    Download sanction letter PDF.
    """
    generator = SanctionLetterGenerator(db)
    
    try:
        pdf_bytes, filename = await generator.get_pdf(application_id)
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/preview/{application_id}")
async def preview_sanction_letter(
    application_id: UUID,
    db: DBSession
):
    """
    Get sanction letter preview data (without generating PDF).
    """
    generator = SanctionLetterGenerator(db)
    
    try:
        preview_data = await generator.get_preview_data(application_id)
        
        return preview_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/verify/{sanction_id}")
async def verify_sanction_letter(
    sanction_id: str,
    db: DBSession
):
    """
    Verify authenticity of a sanction letter by its ID.
    
    Can be used by third parties to validate sanction letters.
    """
    generator = SanctionLetterGenerator(db)
    
    result = await generator.verify_sanction(sanction_id)
    
    if not result:
        return {
            "valid": False,
            "message": "Sanction letter not found or invalid"
        }
    
    return {
        "valid": True,
        "sanction_id": sanction_id,
        "application_number": result.application_number,
        "customer_name": result.customer_name,
        "amount": result.amount,
        "issued_date": result.issued_date.isoformat()
    }
