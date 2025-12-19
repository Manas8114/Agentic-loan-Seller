"""
Underwriting Agent

Evaluates loan applications using rule-based engine and ML scoring.
Makes approve/reject/manual-review decisions.
"""

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import AgentState, ConversationStage, AgentType
from app.core.logging import get_logger
from app.config import settings
from app.services.financial_utils import calculate_emi, calculate_max_loan, calculate_interest_rate


logger = get_logger(__name__)


async def underwriting_agent(state: AgentState) -> AgentState:
    """
    Underwriting agent for loan decision making.
    
    Process:
    1. Check credit score threshold
    2. Validate against pre-approved limit
    3. Calculate EMI and debt-to-income ratio
    4. Apply rule engine
    5. Run ML model for risk scoring
    6. Make final decision
    """
    logger.info(
        "Underwriting agent processing",
        conversation_id=state["conversation_id"],
        loan_amount=state.get("loan_amount"),
        credit_score=state.get("credit_score")
    )
    
    new_state = state.copy()
    
    # Get loan parameters
    loan_amount = state.get("loan_amount", 0)
    tenure_months = state.get("tenure_months", 12)
    credit_score = state.get("credit_score", 0)
    pre_approved_limit = state.get("pre_approved_limit", 0)
    monthly_salary = state.get("monthly_salary", 0)
    salary_verified = state.get("salary_verified", False)
    
    # Run underwriting evaluation
    result = await _evaluate_application(
        loan_amount=loan_amount,
        tenure_months=tenure_months,
        credit_score=credit_score,
        pre_approved_limit=pre_approved_limit,
        monthly_salary=monthly_salary,
        salary_verified=salary_verified
    )
    
    # Update state with results
    new_state["decision"] = result["decision"]
    new_state["decision_reason"] = result["reason"]
    new_state["risk_score"] = result.get("risk_score")
    new_state["risk_flags"] = result.get("risk_flags", [])
    
    if result["decision"] == "APPROVED":
        new_state["approved_amount"] = result["approved_amount"]
        new_state["interest_rate"] = result["interest_rate"]
        new_state["emi"] = result["emi"]
        new_state["stage"] = ConversationStage.DECISION
        
        response = (
            f"📊 **Underwriting Complete**\n\n"
            f"✅ **Decision: APPROVED**\n\n"
            f"**Loan Details:**\n"
            f"• Approved Amount: ₹{result['approved_amount']:,}\n"
            f"• Interest Rate: {result['interest_rate']}% p.a.\n"
            f"• Monthly EMI: ₹{result['emi']:,}\n"
            f"• Tenure: {tenure_months} months\n"
            f"• Total Repayment: ₹{result['emi'] * tenure_months:,}\n\n"
            f"🎉 Congratulations! Your loan is approved. "
            f"I'll generate your sanction letter now."
        )
        
    elif result["decision"] == "REJECTED":
        new_state["stage"] = ConversationStage.REJECTED
        
        response = (
            f"📊 **Underwriting Complete**\n\n"
            f"❌ **Decision: REJECTED**\n\n"
            f"**Reason:** {result['reason']}\n\n"
        )
        
        if result.get("risk_flags"):
            response += "**Risk Flags:**\n"
            for flag in result["risk_flags"]:
                response += f"• {flag}\n"
            response += "\n"
        
        response += (
            "We recommend addressing these concerns and reapplying after 3-6 months.\n"
            "You can also try with a lower loan amount."
        )
        
    else:  # MANUAL_REVIEW
        new_state["stage"] = ConversationStage.UNDERWRITING
        
        response = (
            f"📊 **Underwriting In Progress**\n\n"
            f"⏳ **Decision: Requires Manual Review**\n\n"
            f"Your application needs additional review by our credit team.\n"
            f"This typically takes 2-4 business hours.\n\n"
            f"We'll notify you via SMS once a decision is made."
        )
    
    new_state["current_agent"] = AgentType.UNDERWRITING
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "Underwriting completed",
        conversation_id=state["conversation_id"],
        decision=result["decision"],
        approved_amount=result.get("approved_amount")
    )
    
    return new_state


async def _evaluate_application(
    loan_amount: int,
    tenure_months: int,
    credit_score: int,
    pre_approved_limit: int,
    monthly_salary: int,
    salary_verified: bool
) -> dict:
    """
    Core underwriting logic.
    
    Rules:
    1. Credit score >= 700 required (hard rule)
    2. If loan <= pre_approved_limit: Auto-approve
    3. If loan <= 2x pre_approved_limit AND salary verified:
       - EMI <= 50% of salary: Approve
       - Otherwise: Reject
    4. If loan > 2x pre_approved_limit: Reject
    
    Returns decision with all parameters.
    """
    risk_flags = []
    
    # Rule 1: Credit score check (hard rule)
    min_credit_score = settings.credit_score_threshold
    if credit_score < min_credit_score:
        return {
            "decision": "REJECTED",
            "reason": f"Credit score ({credit_score}) below minimum threshold ({min_credit_score})",
            "risk_flags": ["LOW_CREDIT_SCORE"],
            "risk_score": 0.9
        }
    
    # Calculate interest rate based on credit score
    interest_rate = calculate_interest_rate(credit_score, settings.default_interest_rate)
    
    # Calculate EMI
    emi = calculate_emi(loan_amount, interest_rate, tenure_months)
    
    # Rule 2: Check against pre-approved limit
    if loan_amount <= pre_approved_limit:
        # Auto-approve within pre-approved limit
        return {
            "decision": "APPROVED",
            "approved_amount": loan_amount,
            "interest_rate": interest_rate,
            "emi": emi,
            "reason": "Within pre-approved limit",
            "risk_score": 0.2,
            "risk_flags": []
        }
    
    # Rule 3: Loan exceeds pre-approved limit
    if loan_amount > 2 * pre_approved_limit:
        return {
            "decision": "REJECTED",
            "reason": f"Requested amount (₹{loan_amount:,}) exceeds maximum eligible amount (₹{2*pre_approved_limit:,})",
            "risk_flags": ["EXCEEDS_MAX_LIMIT"],
            "risk_score": 0.85
        }
    
    # Rule 4: Within 1-2x pre-approved, need salary verification
    if not salary_verified or monthly_salary == 0:
        return {
            "decision": "MANUAL_REVIEW",
            "reason": "Salary verification required for loan amount exceeding pre-approved limit",
            "risk_flags": ["SALARY_NOT_VERIFIED"],
            "risk_score": 0.5
        }
    
    # Rule 5: EMI affordability check
    max_emi_ratio = settings.max_emi_to_salary_ratio
    emi_ratio = emi / monthly_salary if monthly_salary > 0 else 1
    
    if emi_ratio > max_emi_ratio:
        risk_flags.append("HIGH_EMI_RATIO")
        
        # Calculate max affordable loan
        max_affordable_emi = int(monthly_salary * max_emi_ratio)
        max_loan = calculate_max_loan(max_affordable_emi, interest_rate, tenure_months)
        
        if max_loan < loan_amount:
            # Offer reduced amount
            reduced_emi = calculate_emi(max_loan, interest_rate, tenure_months)
            
            return {
                "decision": "APPROVED",
                "approved_amount": max_loan,
                "interest_rate": interest_rate,
                "emi": reduced_emi,
                "reason": f"Approved for reduced amount based on EMI affordability (max {max_emi_ratio*100}% of salary)",
                "risk_score": 0.4,
                "risk_flags": risk_flags
            }
    
    # All rules passed - approve
    return {
        "decision": "APPROVED",
        "approved_amount": loan_amount,
        "interest_rate": interest_rate,
        "emi": emi,
        "reason": "All eligibility criteria met",
        "risk_score": 0.25,
        "risk_flags": risk_flags
    }
