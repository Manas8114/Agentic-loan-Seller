"""
Financial Utilities

Shared financial calculation functions used across the application.
Prevents code duplication and ensures consistent calculations.
"""

from typing import Tuple


def calculate_emi(principal: int, annual_rate: float, months: int) -> int:
    """
    Calculate Equated Monthly Installment (EMI).
    
    Formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    Where:
        P = Principal amount
        r = Monthly interest rate (annual_rate / 12 / 100)
        n = Tenure in months
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate as percentage (e.g., 12.5)
        months: Loan tenure in months
    
    Returns:
        Monthly EMI amount as integer (rounded)
    """
    monthly_rate = annual_rate / 12 / 100
    
    if monthly_rate == 0:
        return int(principal / months)
    
    emi_factor = (1 + monthly_rate) ** months
    emi = principal * monthly_rate * emi_factor / (emi_factor - 1)
    
    return int(emi)


def calculate_max_loan(max_emi: int, annual_rate: float, months: int) -> int:
    """
    Calculate maximum loan amount for a given EMI capacity.
    
    Reverse of EMI formula to find maximum principal.
    
    Args:
        max_emi: Maximum affordable monthly EMI
        annual_rate: Annual interest rate as percentage
        months: Loan tenure in months
    
    Returns:
        Maximum loan amount (rounded to nearest 1000)
    """
    monthly_rate = annual_rate / 12 / 100
    
    if monthly_rate == 0:
        return max_emi * months
    
    emi_factor = (1 + monthly_rate) ** months
    principal = max_emi * (emi_factor - 1) / (monthly_rate * emi_factor)
    
    # Round to nearest 1000
    return int(principal / 1000) * 1000


def calculate_loan_details(
    principal: int,
    annual_rate: float,
    months: int
) -> Tuple[int, int, int]:
    """
    Calculate comprehensive loan details.
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate as percentage
        months: Loan tenure in months
    
    Returns:
        Tuple of (emi, total_payment, total_interest)
    """
    emi = calculate_emi(principal, annual_rate, months)
    total_payment = emi * months
    total_interest = total_payment - principal
    
    return emi, total_payment, total_interest


def calculate_interest_rate(credit_score: int, base_rate: float = 12.5) -> float:
    """
    Calculate interest rate based on credit score.
    
    Better credit scores result in lower interest rates.
    
    Args:
        credit_score: Customer's credit score (300-900)
        base_rate: Base annual interest rate
    
    Returns:
        Adjusted annual interest rate
    """
    if credit_score >= 800:
        return base_rate - 2.0
    elif credit_score >= 750:
        return base_rate - 1.0
    elif credit_score >= 700:
        return base_rate
    else:
        return base_rate + 2.0
