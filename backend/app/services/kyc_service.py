"""
KYC Service

Business logic for customer KYC verification.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.customer import KYCVerifyResponse
from app.models.customer import Customer
from app.mock_data.customers import MOCK_CUSTOMERS
from app.core.logging import get_logger
from app.core.security import hash_aadhar


logger = get_logger(__name__)


class KYCService:
    """Service for KYC verification operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def verify_customer(
        self,
        customer_id: UUID,
        pan: str,
        aadhar_last_four: str
    ) -> KYCVerifyResponse:
        """
        Verify customer KYC against CRM database.
        
        Args:
            customer_id: Customer ID to verify
            pan: PAN card number
            aadhar_last_four: Last 4 digits of Aadhar
        
        Returns:
            KYCVerifyResponse with verification result
        """
        # First check mock data
        customer_data = self._find_in_mock_data(pan)
        
        if not customer_data:
            # Check database
            customer_data = await self._find_in_database(customer_id, pan)
        
        if not customer_data:
            return KYCVerifyResponse(
                customer_id=customer_id,
                verified=False,
                message="Customer not found with provided PAN"
            )
        
        # Verify Aadhar last 4 if available
        if customer_data.get("aadhar_last_four"):
            if customer_data["aadhar_last_four"] != aadhar_last_four:
                return KYCVerifyResponse(
                    customer_id=customer_id,
                    verified=False,
                    message="Aadhar last 4 digits do not match"
                )
        
        # KYC verified successfully
        return KYCVerifyResponse(
            customer_id=UUID(customer_data["id"]) if isinstance(customer_data["id"], str) else customer_data["id"],
            verified=True,
            message="KYC verification successful",
            pre_approved_limit=customer_data.get("pre_approved_limit", 0),
            credit_score=customer_data.get("credit_score"),
            kyc_verified_at=datetime.utcnow()
        )
    
    async def get_status(self, customer_id: UUID) -> Optional[dict]:
        """Get KYC status for a customer."""
        # Check database first
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if customer:
            return {
                "customer_id": str(customer.id),
                "kyc_verified": customer.kyc_verified,
                "kyc_verified_at": customer.kyc_verified_at,
                "pan_masked": customer.masked_pan
            }
        
        # Check mock data
        for c in MOCK_CUSTOMERS:
            if c["id"] == str(customer_id):
                return {
                    "customer_id": c["id"],
                    "kyc_verified": c.get("kyc_verified", False),
                    "pan_masked": f"XXXXXX{c['pan'][-4:]}"
                }
        
        return None
    
    async def find_by_phone(self, phone: str):
        """
        Find customer by phone number.
        
        Returns:
            Customer model from database, or a duck-typed object with same 
            attributes (id, name, phone, kyc_verified, pre_approved_limit) 
            from mock data. Returns None if not found.
        """
        # Check database
        result = await self.db.execute(
            select(Customer).where(Customer.phone == phone)
        )
        customer = result.scalar_one_or_none()
        
        if customer:
            return customer
        
        # Check mock data and create temporary customer-like object
        for c in MOCK_CUSTOMERS:
            if c["phone"] == phone:
                # Return as a SimpleNamespace for duck-typing compatibility
                from types import SimpleNamespace
                return SimpleNamespace(
                    id=UUID(c["id"]),
                    name=c["name"],
                    phone=c["phone"],
                    kyc_verified=c.get("kyc_verified", False),
                    pre_approved_limit=c.get("pre_approved_limit", 0)
                )
        
        return None
    
    def _find_in_mock_data(self, pan: str) -> Optional[dict]:
        """Search for customer in mock data by PAN."""
        pan_upper = pan.upper()
        
        for customer in MOCK_CUSTOMERS:
            if customer.get("pan", "").upper() == pan_upper:
                return customer
        
        return None
    
    async def _find_in_database(
        self,
        customer_id: UUID,
        pan: str
    ) -> Optional[dict]:
        """Search for customer in database."""
        result = await self.db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.pan == pan.upper()
            )
        )
        customer = result.scalar_one_or_none()
        
        if customer:
            return {
                "id": customer.id,
                "name": customer.name,
                "pan": customer.pan,
                "aadhar_last_four": None,  # Not stored in plain text
                "pre_approved_limit": customer.pre_approved_limit,
                "credit_score": customer.credit_score
            }
        
        return None
