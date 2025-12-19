"""
Loan Schemes Mock Data

10 realistic synthetic Indian bank/NBFC personal loan schemes for testing.
These are SYNTHETIC schemes for demo purposes only - not actual bank offers.
"""

from typing import List, TypedDict, Optional
from enum import Enum


class EmploymentType(str, Enum):
    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"
    BUSINESS = "business"
    PROFESSIONAL = "professional"


class LoanPurpose(str, Enum):
    WEDDING = "wedding"
    MEDICAL = "medical"
    EDUCATION = "education"
    HOME_RENOVATION = "home_renovation"
    TRAVEL = "travel"
    DEBT_CONSOLIDATION = "debt_consolidation"
    BUSINESS = "business"
    PERSONAL = "personal"
    EMERGENCY = "emergency"


class LoanScheme(TypedDict):
    """Schema for a loan scheme."""
    scheme_id: str
    bank_name: str
    scheme_name: str
    bank_type: str  # "bank" or "nbfc"
    
    # Interest rates
    interest_rate_min: float
    interest_rate_max: float
    
    # Loan amount limits
    min_loan_amount: int
    max_loan_amount: int
    
    # Tenure limits (months)
    min_tenure_months: int
    max_tenure_months: int
    
    # Eligibility criteria
    min_credit_score: int
    min_monthly_income: int
    min_age: int
    max_age: int
    eligible_employment: List[str]
    
    # Fees
    processing_fee_percent: float
    processing_fee_flat: Optional[int]  # None means percentage applies
    
    # Special features
    special_offers: List[str]
    target_purposes: List[str]
    risk_notes: List[str]
    
    # Status
    is_active: bool
    priority_score: int  # Bank's internal priority (1-10)


# ============================================================================
# SYNTHETIC LOAN SCHEMES - 10 Indian Bank/NBFC Personal Loans
# ============================================================================

LOAN_SCHEMES: List[LoanScheme] = [
    # 1. HDFC Bank - Premium offering
    {
        "scheme_id": "HDFC_SMART_01",
        "bank_name": "HDFC Bank",
        "scheme_name": "Smart Personal Loan",
        "bank_type": "bank",
        "interest_rate_min": 10.50,
        "interest_rate_max": 14.00,
        "min_loan_amount": 50000,
        "max_loan_amount": 4000000,
        "min_tenure_months": 12,
        "max_tenure_months": 60,
        "min_credit_score": 750,
        "min_monthly_income": 25000,
        "min_age": 21,
        "max_age": 60,
        "eligible_employment": ["salaried", "self_employed", "professional"],
        "processing_fee_percent": 0.0,  # Zero processing fee offer
        "processing_fee_flat": None,
        "special_offers": [
            "Zero Processing Fee",
            "Instant Approval for Pre-approved",
            "Balance Transfer Available"
        ],
        "target_purposes": ["wedding", "home_renovation", "travel", "personal"],
        "risk_notes": [],
        "is_active": True,
        "priority_score": 9
    },
    
    # 2. SBI - Government bank, competitive rates
    {
        "scheme_id": "SBI_XPRESS_01",
        "bank_name": "State Bank of India",
        "scheme_name": "Xpress Credit",
        "bank_type": "bank",
        "interest_rate_min": 10.00,
        "interest_rate_max": 12.50,
        "min_loan_amount": 25000,
        "max_loan_amount": 2000000,
        "min_tenure_months": 12,
        "max_tenure_months": 72,
        "min_credit_score": 680,
        "min_monthly_income": 15000,
        "min_age": 21,
        "max_age": 65,
        "eligible_employment": ["salaried"],
        "processing_fee_percent": 1.0,
        "processing_fee_flat": None,
        "special_offers": [
            "Lowest Interest for Govt Employees",
            "Longer Tenure Available",
            "No Collateral Required"
        ],
        "target_purposes": ["medical", "education", "wedding", "emergency"],
        "risk_notes": ["Processing time 3-5 days"],
        "is_active": True,
        "priority_score": 8
    },
    
    # 3. ICICI Bank - Fast disbursement
    {
        "scheme_id": "ICICI_INSTANT_01",
        "bank_name": "ICICI Bank",
        "scheme_name": "Instant Personal Loan",
        "bank_type": "bank",
        "interest_rate_min": 11.00,
        "interest_rate_max": 15.00,
        "min_loan_amount": 50000,
        "max_loan_amount": 2500000,
        "min_tenure_months": 12,
        "max_tenure_months": 60,
        "min_credit_score": 700,
        "min_monthly_income": 20000,
        "min_age": 23,
        "max_age": 58,
        "eligible_employment": ["salaried", "self_employed"],
        "processing_fee_percent": 2.0,
        "processing_fee_flat": None,
        "special_offers": [
            "2-Hour Disbursement",
            "Paperless Process",
            "Flexible EMI Dates"
        ],
        "target_purposes": ["personal", "travel", "home_renovation"],
        "risk_notes": ["Higher processing fee"],
        "is_active": True,
        "priority_score": 8
    },
    
    # 4. Axis Bank - Balanced offering
    {
        "scheme_id": "AXIS_EXPRESS_01",
        "bank_name": "Axis Bank",
        "scheme_name": "Express Personal Loan",
        "bank_type": "bank",
        "interest_rate_min": 11.50,
        "interest_rate_max": 16.00,
        "min_loan_amount": 50000,
        "max_loan_amount": 1500000,
        "min_tenure_months": 12,
        "max_tenure_months": 60,
        "min_credit_score": 650,
        "min_monthly_income": 15000,
        "min_age": 21,
        "max_age": 60,
        "eligible_employment": ["salaried", "self_employed", "business"],
        "processing_fee_percent": 1.5,
        "processing_fee_flat": None,
        "special_offers": [
            "Pre-approved Offers",
            "Step-up EMI Option",
            "Top-up Loan Available"
        ],
        "target_purposes": ["wedding", "personal", "debt_consolidation"],
        "risk_notes": [],
        "is_active": True,
        "priority_score": 7
    },
    
    # 5. Bajaj Finserv - NBFC, flexible
    {
        "scheme_id": "BAJAJ_FLEXI_01",
        "bank_name": "Bajaj Finserv",
        "scheme_name": "Flexi Personal Loan",
        "bank_type": "nbfc",
        "interest_rate_min": 12.00,
        "interest_rate_max": 17.00,
        "min_loan_amount": 100000,
        "max_loan_amount": 3500000,
        "min_tenure_months": 12,
        "max_tenure_months": 60,
        "min_credit_score": 720,
        "min_monthly_income": 25000,
        "min_age": 25,
        "max_age": 55,
        "eligible_employment": ["salaried", "self_employed", "professional"],
        "processing_fee_percent": 0.0,
        "processing_fee_flat": 4999,
        "special_offers": [
            "Flexi Loan - Pay Interest Only",
            "Withdraw as Needed",
            "No Foreclosure Charges"
        ],
        "target_purposes": ["business", "wedding", "home_renovation"],
        "risk_notes": ["Higher interest for lower scores"],
        "is_active": True,
        "priority_score": 7
    },
    
    # 6. Kotak Mahindra - Premium segment
    {
        "scheme_id": "KOTAK_PRIME_01",
        "bank_name": "Kotak Mahindra Bank",
        "scheme_name": "Prime Personal Loan",
        "bank_type": "bank",
        "interest_rate_min": 10.75,
        "interest_rate_max": 14.50,
        "min_loan_amount": 75000,
        "max_loan_amount": 3000000,
        "min_tenure_months": 12,
        "max_tenure_months": 60,
        "min_credit_score": 725,
        "min_monthly_income": 30000,
        "min_age": 21,
        "max_age": 58,
        "eligible_employment": ["salaried"],
        "processing_fee_percent": 2.5,
        "processing_fee_flat": None,
        "special_offers": [
            "Zero Prepayment Charges",
            "Dedicated Relationship Manager",
            "Priority Processing"
        ],
        "target_purposes": ["travel", "wedding", "personal"],
        "risk_notes": ["High processing fee"],
        "is_active": True,
        "priority_score": 6
    },
    
    # 7. Tata Capital - NBFC, competitive
    {
        "scheme_id": "TATA_VALUE_01",
        "bank_name": "Tata Capital",
        "scheme_name": "Value Personal Loan",
        "bank_type": "nbfc",
        "interest_rate_min": 11.50,
        "interest_rate_max": 18.00,
        "min_loan_amount": 50000,
        "max_loan_amount": 2500000,
        "min_tenure_months": 12,
        "max_tenure_months": 72,
        "min_credit_score": 650,
        "min_monthly_income": 18000,
        "min_age": 21,
        "max_age": 60,
        "eligible_employment": ["salaried", "self_employed", "business"],
        "processing_fee_percent": 1.5,
        "processing_fee_flat": None,
        "special_offers": [
            "Women Borrowers Discount",
            "Festival Offers",
            "Quick Turnaround"
        ],
        "target_purposes": ["medical", "education", "emergency", "wedding"],
        "risk_notes": ["Higher rates for self-employed"],
        "is_active": True,
        "priority_score": 6
    },
    
    # 8. IDFC First - Digital-first
    {
        "scheme_id": "IDFC_DIGITAL_01",
        "bank_name": "IDFC First Bank",
        "scheme_name": "Digital Personal Loan",
        "bank_type": "bank",
        "interest_rate_min": 10.49,
        "interest_rate_max": 15.00,
        "min_loan_amount": 20000,
        "max_loan_amount": 1000000,
        "min_tenure_months": 6,
        "max_tenure_months": 48,
        "min_credit_score": 700,
        "min_monthly_income": 20000,
        "min_age": 23,
        "max_age": 55,
        "eligible_employment": ["salaried"],
        "processing_fee_percent": 0.0,
        "processing_fee_flat": 999,
        "special_offers": [
            "100% Digital Process",
            "Instant Approval",
            "Low Documentation"
        ],
        "target_purposes": ["personal", "travel", "emergency"],
        "risk_notes": ["Lower max amount", "Shorter tenure"],
        "is_active": True,
        "priority_score": 7
    },
    
    # 9. IndusInd Bank - Flexible EMI
    {
        "scheme_id": "INDUS_FLEX_01",
        "bank_name": "IndusInd Bank",
        "scheme_name": "Flex Pay Personal Loan",
        "bank_type": "bank",
        "interest_rate_min": 11.00,
        "interest_rate_max": 16.00,
        "min_loan_amount": 30000,
        "max_loan_amount": 1500000,
        "min_tenure_months": 12,
        "max_tenure_months": 60,
        "min_credit_score": 675,
        "min_monthly_income": 20000,
        "min_age": 21,
        "max_age": 60,
        "eligible_employment": ["salaried", "self_employed"],
        "processing_fee_percent": 2.0,
        "processing_fee_flat": None,
        "special_offers": [
            "Step-up EMI",
            "Step-down EMI",
            "Balloon Payment Option"
        ],
        "target_purposes": ["debt_consolidation", "personal", "medical"],
        "risk_notes": [],
        "is_active": True,
        "priority_score": 6
    },
    
    # 10. Fullerton India - NBFC, wider eligibility
    {
        "scheme_id": "FULL_SMART_01",
        "bank_name": "Fullerton India",
        "scheme_name": "Smart Cash Loan",
        "bank_type": "nbfc",
        "interest_rate_min": 14.00,
        "interest_rate_max": 24.00,
        "min_loan_amount": 25000,
        "max_loan_amount": 500000,
        "min_tenure_months": 12,
        "max_tenure_months": 48,
        "min_credit_score": 600,
        "min_monthly_income": 12000,
        "min_age": 21,
        "max_age": 65,
        "eligible_employment": ["salaried", "self_employed", "business", "professional"],
        "processing_fee_percent": 3.0,
        "processing_fee_flat": None,
        "special_offers": [
            "No Income Proof for Repeat Customers",
            "Doorstep Service",
            "Cash Disbursement"
        ],
        "target_purposes": ["emergency", "medical", "personal"],
        "risk_notes": ["Higher interest rates", "Lower loan amounts"],
        "is_active": True,
        "priority_score": 5
    }
]


def get_all_schemes() -> List[LoanScheme]:
    """Get all active loan schemes."""
    return [s for s in LOAN_SCHEMES if s["is_active"]]


def get_scheme_by_id(scheme_id: str) -> Optional[LoanScheme]:
    """Get a specific scheme by ID."""
    for scheme in LOAN_SCHEMES:
        if scheme["scheme_id"] == scheme_id:
            return scheme
    return None
