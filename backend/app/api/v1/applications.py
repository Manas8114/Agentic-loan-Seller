"""
Loan Applications Routes

Admin routes for viewing and managing loan applications.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.schemas.loan import LoanApplicationResponse, ApplicationStatusEnum
from app.api.deps import DBSession, CurrentAdminUser
from app.models.loan_application import LoanApplication, ApplicationStatus
from app.models.customer import Customer
from app.core.logging import get_logger


router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=List[LoanApplicationResponse])
async def list_applications(
    db: DBSession,
    current_user: CurrentAdminUser,
    status_filter: Optional[ApplicationStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|amount|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
):
    """
    List all loan applications with filters.
    
    Admin only endpoint.
    """
    query = select(LoanApplication).options(selectinload(LoanApplication.customer))
    
    # Apply status filter
    if status_filter:
        query = query.where(LoanApplication.status == status_filter.value)
    
    # Apply sorting
    sort_column = getattr(LoanApplication, sort_by, LoanApplication.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    # Transform to response format
    return [
        LoanApplicationResponse(
            id=app.id,
            application_number=app.application_number,
            customer_id=app.customer_id,
            customer_name=app.customer.name if app.customer else None,
            requested_amount=app.requested_amount,
            approved_amount=app.approved_amount,
            tenure_months=app.tenure_months,
            interest_rate=float(app.interest_rate) if app.interest_rate else None,
            emi=app.emi,
            loan_purpose=app.loan_purpose,
            status=ApplicationStatusEnum(app.status.value),
            decision_reason=app.decision_reason,
            sanction_letter_url=app.sanction_letter_url,
            created_at=app.created_at,
            updated_at=app.updated_at
        )
        for app in applications
    ]


@router.get("/stats")
async def get_application_stats(
    db: DBSession,
    current_user: CurrentAdminUser
):
    """
    Get application statistics for dashboard.
    """
    # Total count by status
    status_counts = {}
    for status in ApplicationStatus:
        result = await db.execute(
            select(func.count(LoanApplication.id)).where(
                LoanApplication.status == status
            )
        )
        status_counts[status.value] = result.scalar() or 0
    
    # Total amount sanctioned
    result = await db.execute(
        select(func.sum(LoanApplication.approved_amount)).where(
            LoanApplication.status == ApplicationStatus.SANCTIONED
        )
    )
    total_sanctioned = result.scalar() or 0
    
    # Today's applications
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count(LoanApplication.id)).where(
            func.date(LoanApplication.created_at) == today
        )
    )
    today_count = result.scalar() or 0
    
    return {
        "status_breakdown": status_counts,
        "total_applications": sum(status_counts.values()),
        "total_sanctioned_amount": total_sanctioned,
        "today_applications": today_count,
        "approval_rate": _calculate_approval_rate(status_counts)
    }


@router.get("/{application_id}", response_model=LoanApplicationResponse)
async def get_application(
    application_id: UUID,
    db: DBSession,
    current_user: CurrentAdminUser
):
    """
    Get single application details.
    """
    result = await db.execute(
        select(LoanApplication)
        .options(selectinload(LoanApplication.customer))
        .where(LoanApplication.id == application_id)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    return LoanApplicationResponse(
        id=app.id,
        application_number=app.application_number,
        customer_id=app.customer_id,
        customer_name=app.customer.name if app.customer else None,
        requested_amount=app.requested_amount,
        approved_amount=app.approved_amount,
        tenure_months=app.tenure_months,
        interest_rate=float(app.interest_rate) if app.interest_rate else None,
        emi=app.emi,
        loan_purpose=app.loan_purpose,
        status=ApplicationStatusEnum(app.status.value),
        decision_reason=app.decision_reason,
        sanction_letter_url=app.sanction_letter_url,
        created_at=app.created_at,
        updated_at=app.updated_at
    )


@router.get("/{application_id}/audit-trail")
async def get_application_audit_trail(
    application_id: UUID,
    db: DBSession,
    current_user: CurrentAdminUser
):
    """
    Get audit trail for an application.
    """
    from app.models.audit_log import AuditLog
    
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.application_id == application_id)
        .order_by(desc(AuditLog.timestamp))
    )
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "agent_name": log.agent_name,
            "timestamp": log.timestamp.isoformat(),
            "status": log.status,
            "confidence_score": float(log.confidence_score) if log.confidence_score else None
        }
        for log in logs
    ]


def _calculate_approval_rate(status_counts: dict) -> float:
    """Calculate approval rate percentage."""
    approved = status_counts.get("APPROVED", 0) + status_counts.get("SANCTIONED", 0)
    rejected = status_counts.get("REJECTED", 0)
    total = approved + rejected
    
    if total == 0:
        return 0.0
    
    return round((approved / total) * 100, 2)
