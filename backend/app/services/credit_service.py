"""
Credit Service

Mock credit bureau integration for fetching credit scores.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.loan import CreditScoreResponse
from app.models.customer import Customer
from app.mock_data.customers import MOCK_CUSTOMERS, MOCK_CREDIT_SCORES
from app.core.logging import get_logger


logger = get_logger(__name__)


class CreditService:
    """Service for credit bureau operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_credit_report(self, customer_id: UUID) -> CreditScoreResponse:
        """
        Fetch credit report for a customer.
        
        Args:
            customer_id: Customer UUID
        
        Returns:
            CreditScoreResponse with full credit data
        
        Raises:
            ValueError: If customer not found
        """
        # Find customer
        customer = await self._get_customer(customer_id)
        
        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")
        
        # Get credit data from mock bureau
        pan = customer.get("pan", "")
        credit_data = MOCK_CREDIT_SCORES.get(pan.upper(), {})
        
        if not credit_data:
            # Generate default credit data
            credit_data = self._generate_default_credit_data(customer)
        
        return CreditScoreResponse(
            customer_id=customer_id,
            credit_score=credit_data.get("credit_score", 700),
            score_date=datetime.utcnow(),
            active_accounts=credit_data.get("active_accounts", 2),
            total_outstanding=credit_data.get("total_outstanding", 0),
            delinquent_accounts=credit_data.get("delinquent_accounts", 0),
            credit_utilization=credit_data.get("credit_utilization", 0.3),
            payment_history_score=credit_data.get("payment_history_score", 85)
        )
    
    async def refresh_credit_score(self, customer_id: UUID) -> CreditScoreResponse:
        """
        Refresh credit score from bureau.
        
        In production, this would make an actual API call.
        """
        logger.info(f"Refreshing credit score for customer: {customer_id}")
        
        # Simulate bureau call
        return await self.get_credit_report(customer_id)
    
    async def find_customer_by_pan(self, pan: str) -> Optional[dict]:
        """Find customer by PAN number."""
        pan_upper = pan.upper()
        
        # Check mock data
        for customer in MOCK_CUSTOMERS:
            if customer.get("pan", "").upper() == pan_upper:
                return {
                    "id": UUID(customer["id"]),
                    "name": customer["name"],
                    "pan": customer["pan"]
                }
        
        # Check database
        result = await self.db.execute(
            select(Customer).where(Customer.pan == pan_upper)
        )
        customer = result.scalar_one_or_none()
        
        if customer:
            return {
                "id": customer.id,
                "name": customer.name,
                "pan": customer.pan
            }
        
        return None
    
    async def _get_customer(self, customer_id: UUID) -> Optional[dict]:
        """Get customer data by ID."""
        # Check database
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if customer:
            return {
                "id": customer.id,
                "name": customer.name,
                "pan": customer.pan,
                "credit_score": customer.credit_score
            }
        
        # Check mock data
        for c in MOCK_CUSTOMERS:
            if c["id"] == str(customer_id):
                return c
        
        return None
    
    def _generate_default_credit_data(self, customer: dict) -> dict:
        """Generate default credit data for customers not in mock bureau."""
        return {
            "credit_score": customer.get("credit_score", 700),
            "active_accounts": 2,
            "total_outstanding": 100000,
            "delinquent_accounts": 0,
            "credit_utilization": 0.30,
            "payment_history_score": 85
        }
