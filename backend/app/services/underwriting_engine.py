"""
Underwriting Engine Service

Rule-based and ML-powered underwriting logic.
"""

from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.loan import UnderwritingRequest, UnderwritingResponse, RuleEngineResult
from app.models.loan_application import LoanApplication
from app.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class UnderwritingRule:
    """Definition of an underwriting rule."""
    name: str
    description: str
    is_hard_rule: bool  # Hard rules cause immediate rejection


class UnderwritingEngine:
    """
    Loan underwriting engine with rules and ML scoring.
    
    Implements:
    - Rule-based evaluation
    - EMI calculation
    - Risk scoring
    - ML model integration (optional)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.credit_threshold = settings.credit_score_threshold
        self.max_emi_ratio = settings.max_emi_to_salary_ratio
        self.default_rate = settings.default_interest_rate
    
    async def evaluate(self, request: UnderwritingRequest) -> UnderwritingResponse:
        """
        Evaluate a loan application.
        
        Process:
        1. Run all underwriting rules
        2. Calculate EMI and ratios
        3. Apply ML scoring (if available)
        4. Make final decision
        """
        logger.info(
            "Evaluating application",
            application_id=str(request.application_id),
            amount=request.requested_amount
        )
        
        rules_results = []
        risk_flags = []
        
        # Rule 1: Credit Score Check
        credit_result = self._check_credit_score(request.credit_score)
        rules_results.append(credit_result)
        
        if not credit_result.passed:
            risk_flags.append("LOW_CREDIT_SCORE")
            return UnderwritingResponse(
                application_id=request.application_id,
                decision="REJECTED",
                rules_result=rules_results,
                risk_flags=risk_flags,
                decision_reason=credit_result.message,
                confidence=0.95
            )
        
        # Rule 2: Pre-approved Limit Check
        limit_result = self._check_pre_approved_limit(
            request.requested_amount,
            request.pre_approved_limit
        )
        rules_results.append(limit_result)
        
        # Calculate interest rate based on credit score
        interest_rate = self._calculate_interest_rate(request.credit_score)
        
        # Calculate EMI
        emi = self._calculate_emi(
            request.requested_amount,
            interest_rate,
            request.tenure_months
        )
        
        # Rule 3: EMI Affordability
        emi_result = self._check_emi_affordability(
            emi,
            request.monthly_salary,
            request.existing_emi or 0
        )
        rules_results.append(emi_result)
        
        if not emi_result.passed:
            risk_flags.append("HIGH_EMI_RATIO")
        
        # Determine approved amount
        if limit_result.passed and emi_result.passed:
            approved_amount = request.requested_amount
            decision = "APPROVED"
            reason = "All eligibility criteria met"
        elif limit_result.passed:
            # Calculate max affordable loan
            max_emi = int(request.monthly_salary * self.max_emi_ratio) - (request.existing_emi or 0)
            max_loan = self._calculate_max_loan(max_emi, interest_rate, request.tenure_months)
            
            if max_loan >= request.requested_amount * 0.5:
                approved_amount = max_loan
                emi = self._calculate_emi(max_loan, interest_rate, request.tenure_months)
                decision = "APPROVED"
                reason = f"Approved for reduced amount based on EMI affordability"
            else:
                approved_amount = None
                decision = "REJECTED"
                reason = "Insufficient repayment capacity"
        else:
            # Exceeds pre-approved limit
            if request.requested_amount <= 2 * request.pre_approved_limit:
                decision = "MANUAL_REVIEW"
                approved_amount = None
                reason = "Requires manual review - amount exceeds pre-approved limit"
            else:
                decision = "REJECTED"
                approved_amount = None
                reason = "Requested amount exceeds maximum eligible limit"
                risk_flags.append("EXCEEDS_MAX_LIMIT")
        
        # ML Risk Score (simplified)
        risk_score = self._calculate_risk_score(request)
        
        return UnderwritingResponse(
            application_id=request.application_id,
            decision=decision,
            approved_amount=approved_amount,
            interest_rate=interest_rate if decision == "APPROVED" else None,
            emi=emi if decision == "APPROVED" else None,
            risk_score=risk_score,
            ml_probability=1 - risk_score,  # Probability of good repayment
            rules_result=rules_results,
            risk_flags=risk_flags,
            decision_reason=reason,
            confidence=0.85 if decision == "APPROVED" else 0.90
        )
    
    async def get_risk_flags(self, application_id: UUID) -> List[str]:
        """Get risk flags for an application."""
        result = await self.db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        app = result.scalar_one_or_none()
        
        if app and app.risk_flags:
            return app.risk_flags
        
        return []
    
    def _check_credit_score(self, score: int) -> RuleEngineResult:
        """Rule: Credit score must be >= threshold."""
        passed = score >= self.credit_threshold
        
        return RuleEngineResult(
            rule_name="CREDIT_SCORE_CHECK",
            passed=passed,
            message=f"Credit score {score} {'meets' if passed else 'below'} minimum threshold ({self.credit_threshold})",
            value=float(score),
            threshold=float(self.credit_threshold)
        )
    
    def _check_pre_approved_limit(self, amount: int, limit: int) -> RuleEngineResult:
        """Rule: Requested amount should be within pre-approved limit."""
        passed = amount <= limit
        
        return RuleEngineResult(
            rule_name="PRE_APPROVED_LIMIT_CHECK",
            passed=passed,
            message=f"Requested ₹{amount:,} {'within' if passed else 'exceeds'} pre-approved limit ₹{limit:,}",
            value=float(amount),
            threshold=float(limit)
        )
    
    def _check_emi_affordability(
        self,
        emi: int,
        salary: int,
        existing_emi: int
    ) -> RuleEngineResult:
        """Rule: Total EMI should be <= 50% of salary."""
        if salary <= 0:
            return RuleEngineResult(
                rule_name="EMI_AFFORDABILITY_CHECK",
                passed=False,
                message="Salary information not available",
                value=0,
                threshold=self.max_emi_ratio
            )
        
        total_emi = emi + existing_emi
        emi_ratio = total_emi / salary
        passed = emi_ratio <= self.max_emi_ratio
        
        return RuleEngineResult(
            rule_name="EMI_AFFORDABILITY_CHECK",
            passed=passed,
            message=f"EMI ratio {emi_ratio:.2%} {'within' if passed else 'exceeds'} maximum {self.max_emi_ratio:.0%}",
            value=emi_ratio,
            threshold=self.max_emi_ratio
        )
    
    def _calculate_interest_rate(self, credit_score: int) -> float:
        """Calculate interest rate based on credit score."""
        if credit_score >= 800:
            return self.default_rate - 2.0
        elif credit_score >= 750:
            return self.default_rate - 1.0
        elif credit_score >= 700:
            return self.default_rate
        else:
            return self.default_rate + 2.0
    
    def _calculate_emi(self, principal: int, annual_rate: float, months: int) -> int:
        """Calculate EMI using standard formula."""
        monthly_rate = annual_rate / 12 / 100
        
        if monthly_rate == 0:
            return int(principal / months)
        
        emi_factor = (1 + monthly_rate) ** months
        emi = principal * monthly_rate * emi_factor / (emi_factor - 1)
        
        return int(emi)
    
    def _calculate_max_loan(self, max_emi: int, annual_rate: float, months: int) -> int:
        """Calculate maximum loan for given EMI."""
        monthly_rate = annual_rate / 12 / 100
        
        if monthly_rate == 0:
            return max_emi * months
        
        emi_factor = (1 + monthly_rate) ** months
        principal = max_emi * (emi_factor - 1) / (monthly_rate * emi_factor)
        
        return int(principal / 1000) * 1000  # Round to nearest 1000
    
    def _calculate_risk_score(self, request: UnderwritingRequest) -> float:
        """
        Calculate simplified risk score (0-1, lower is better).
        
        In production, this would use a trained ML model.
        """
        score = 0.3  # Base risk
        
        # Credit score factor
        if request.credit_score >= 800:
            score -= 0.1
        elif request.credit_score >= 750:
            score -= 0.05
        elif request.credit_score < 700:
            score += 0.2
        
        # Loan to income ratio
        if request.monthly_salary > 0:
            lti_ratio = request.requested_amount / (request.monthly_salary * 12)
            if lti_ratio > 2:
                score += 0.15
            elif lti_ratio < 1:
                score -= 0.05
        
        # Pre-approved ratio
        if request.pre_approved_limit > 0:
            pa_ratio = request.requested_amount / request.pre_approved_limit
            if pa_ratio > 1.5:
                score += 0.1
            elif pa_ratio <= 1:
                score -= 0.05
        
        return max(0.1, min(0.9, score))
