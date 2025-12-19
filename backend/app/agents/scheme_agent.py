"""
Scheme Recommendation Agent

Compares loan schemes and recommends best options based on customer profile.
Uses weighted scoring algorithm for transparent decision-making.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import AgentState, ConversationStage, AgentType
from app.mock_data.loan_schemes import get_all_schemes, LoanScheme
from app.core.logging import get_logger
from app.services.financial_utils import calculate_emi


logger = get_logger(__name__)


# ============================================================================
# SCORING WEIGHTS
# ============================================================================
SCORING_WEIGHTS = {
    "interest_rate": 0.30,      # Lower is better
    "emi_affordability": 0.25,  # EMI should be < 50% of income
    "credit_match": 0.15,       # Better rates for higher scores
    "processing_fee": 0.10,     # Lower fees preferred
    "purpose_match": 0.10,      # Matches customer purpose
    "special_offers": 0.10,     # Added benefits
}


@dataclass
class SchemeRecommendation:
    """A scored and explained scheme recommendation."""
    scheme: LoanScheme
    score: float
    interest_rate: float  # Calculated rate for customer
    emi: int
    total_cost: int      # Principal + Interest + Fees
    explanation: List[str]
    pros: List[str]
    cons: List[str]


async def scheme_agent(state: AgentState) -> AgentState:
    """
    Scheme Recommendation Agent.
    
    Analyzes customer profile and recommends best loan schemes.
    Called after underwriting approval.
    """
    logger.info(
        "Scheme agent processing",
        conversation_id=state["conversation_id"],
        loan_amount=state.get("loan_amount"),
        credit_score=state.get("credit_score")
    )
    
    # Get last user message
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    new_state = state.copy()
    current_stage = state.get("stage", ConversationStage.SCHEME_RECOMMENDATION)
    
    # Check if user is selecting a scheme
    if current_stage == ConversationStage.SCHEME_RECOMMENDATION:
        # Check if user has made a selection
        selection = _parse_scheme_selection(last_user_message, state)
        if selection:
            return _handle_scheme_selection(new_state, state, selection)
        
        # If recommendations already exist and user didn't select, prompt again
        existing_recs = state.get("scheme_recommendations")
        if existing_recs:
            response = (
                "Please select one of the schemes above:\n"
                "• Reply **'1'** for the best match\n"
                "• Reply **'2'** or **'3'** for alternatives\n"
            )
            new_state["current_agent"] = AgentType.SCHEME
            new_state["messages"] = state["messages"] + [AIMessage(content=response)]
            new_state["stage"] = ConversationStage.SCHEME_RECOMMENDATION
            return new_state
    
    # Generate scheme recommendations (only if none exist)
    recommendations = _generate_recommendations(state)
    
    if not recommendations:
        # No eligible schemes found
        response = _generate_no_schemes_response(state)
        new_state["stage"] = ConversationStage.REJECTED
    else:
        # Store recommendations in state
        new_state["scheme_recommendations"] = [
            {
                "scheme_id": r.scheme["scheme_id"],
                "bank_name": r.scheme["bank_name"],
                "scheme_name": r.scheme["scheme_name"],
                "score": r.score,
                "interest_rate": r.interest_rate,
                "emi": r.emi,
                "total_cost": r.total_cost
            }
            for r in recommendations[:3]
        ]
        new_state["stage"] = ConversationStage.SCHEME_RECOMMENDATION
        response = _generate_recommendations_response(recommendations[:3], state)
    
    new_state["current_agent"] = AgentType.SCHEME
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "Scheme agent completed",
        conversation_id=state["conversation_id"],
        num_recommendations=len(recommendations) if recommendations else 0,
        next_stage=new_state["stage"].value
    )
    
    return new_state


def _generate_recommendations(state: AgentState) -> List[SchemeRecommendation]:
    """Generate scored scheme recommendations based on customer profile."""
    
    # Customer profile
    loan_amount = state.get("loan_amount", 500000)
    tenure_months = state.get("tenure_months", 36)
    credit_score = state.get("credit_score", 700)
    monthly_income = state.get("monthly_salary", 50000)
    loan_purpose = state.get("loan_purpose", "personal")
    employment_type = "salaried"  # Default, could be from state
    age = 30  # Default, could be from state
    
    all_schemes = get_all_schemes()
    recommendations = []
    
    for scheme in all_schemes:
        # Check eligibility first
        eligibility = _check_eligibility(
            scheme, loan_amount, tenure_months, credit_score, 
            monthly_income, employment_type, age
        )
        
        if not eligibility["eligible"]:
            continue
        
        # Calculate actual interest rate for customer
        interest_rate = _calculate_customer_rate(scheme, credit_score)
        
        # Calculate EMI
        emi = calculate_emi(loan_amount, interest_rate, tenure_months)
        
        # Calculate total cost
        processing_fee = _calculate_processing_fee(scheme, loan_amount)
        total_interest = (emi * tenure_months) - loan_amount
        total_cost = loan_amount + total_interest + processing_fee
        
        # Score the scheme
        score, explanations = _score_scheme(
            scheme=scheme,
            interest_rate=interest_rate,
            emi=emi,
            monthly_income=monthly_income,
            credit_score=credit_score,
            loan_purpose=loan_purpose,
            processing_fee=processing_fee,
            loan_amount=loan_amount
        )
        
        # Generate pros and cons
        pros, cons = _generate_pros_cons(scheme, interest_rate, emi, processing_fee)
        
        recommendations.append(SchemeRecommendation(
            scheme=scheme,
            score=score,
            interest_rate=interest_rate,
            emi=emi,
            total_cost=total_cost,
            explanation=explanations,
            pros=pros,
            cons=cons
        ))
    
    # Sort by score (descending)
    recommendations.sort(key=lambda x: x.score, reverse=True)
    
    return recommendations


def _check_eligibility(
    scheme: LoanScheme,
    loan_amount: int,
    tenure_months: int,
    credit_score: int,
    monthly_income: int,
    employment_type: str,
    age: int
) -> Dict:
    """Check if customer is eligible for the scheme."""
    
    reasons = []
    
    if credit_score < scheme["min_credit_score"]:
        reasons.append(f"Credit score {credit_score} below minimum {scheme['min_credit_score']}")
    
    if loan_amount < scheme["min_loan_amount"]:
        reasons.append(f"Amount below minimum ₹{scheme['min_loan_amount']:,}")
    
    if loan_amount > scheme["max_loan_amount"]:
        reasons.append(f"Amount exceeds maximum ₹{scheme['max_loan_amount']:,}")
    
    if tenure_months < scheme["min_tenure_months"]:
        reasons.append(f"Tenure below minimum {scheme['min_tenure_months']} months")
    
    if tenure_months > scheme["max_tenure_months"]:
        reasons.append(f"Tenure exceeds maximum {scheme['max_tenure_months']} months")
    
    if monthly_income < scheme["min_monthly_income"]:
        reasons.append(f"Income below minimum ₹{scheme['min_monthly_income']:,}")
    
    if age < scheme["min_age"] or age > scheme["max_age"]:
        reasons.append(f"Age not in range {scheme['min_age']}-{scheme['max_age']}")
    
    if employment_type not in scheme["eligible_employment"]:
        reasons.append(f"Employment type '{employment_type}' not eligible")
    
    return {
        "eligible": len(reasons) == 0,
        "reasons": reasons
    }


def _calculate_customer_rate(scheme: LoanScheme, credit_score: int) -> float:
    """Calculate personalized interest rate based on credit score."""
    
    min_rate = scheme["interest_rate_min"]
    max_rate = scheme["interest_rate_max"]
    
    # Higher credit score = lower rate
    # 850+ = min rate, 650- = max rate
    score_range = 200  # 850 - 650
    rate_range = max_rate - min_rate
    
    if credit_score >= 850:
        return min_rate
    elif credit_score <= 650:
        return max_rate
    else:
        score_factor = (850 - credit_score) / score_range
        return round(min_rate + (rate_range * score_factor), 2)


def _calculate_processing_fee(scheme: LoanScheme, loan_amount: int) -> int:
    """Calculate processing fee."""
    if scheme["processing_fee_flat"] is not None:
        return scheme["processing_fee_flat"]
    return int(loan_amount * scheme["processing_fee_percent"] / 100)


def _score_scheme(
    scheme: LoanScheme,
    interest_rate: float,
    emi: int,
    monthly_income: int,
    credit_score: int,
    loan_purpose: str,
    processing_fee: int,
    loan_amount: int
) -> Tuple[float, List[str]]:
    """Score the scheme using weighted algorithm."""
    
    explanations = []
    scores = {}
    
    # 1. Interest Rate Score (lower is better)
    # Normalize: 10% = 100, 24% = 0
    rate_score = max(0, min(100, (24 - interest_rate) / 14 * 100))
    scores["interest_rate"] = rate_score
    if rate_score >= 70:
        explanations.append(f"Competitive interest rate at {interest_rate}%")
    
    # 2. EMI Affordability Score
    # EMI should be < 40% of income for high score
    emi_ratio = emi / monthly_income
    if emi_ratio <= 0.3:
        emi_score = 100
        explanations.append("EMI is very affordable (under 30% of income)")
    elif emi_ratio <= 0.4:
        emi_score = 80
        explanations.append("EMI is affordable (under 40% of income)")
    elif emi_ratio <= 0.5:
        emi_score = 60
    else:
        emi_score = max(0, 100 - (emi_ratio * 100))
    scores["emi_affordability"] = emi_score
    
    # 3. Credit Match Score
    # How much buffer above minimum
    credit_buffer = credit_score - scheme["min_credit_score"]
    credit_score_val = min(100, 50 + credit_buffer)
    scores["credit_match"] = credit_score_val
    if credit_buffer >= 50:
        explanations.append("Your credit score qualifies for best rates")
    
    # 4. Processing Fee Score
    fee_percent = (processing_fee / loan_amount) * 100
    if fee_percent == 0:
        fee_score = 100
        explanations.append("Zero processing fee!")
    elif fee_percent <= 1:
        fee_score = 80
    elif fee_percent <= 2:
        fee_score = 60
    else:
        fee_score = max(0, 100 - fee_percent * 20)
    scores["processing_fee"] = fee_score
    
    # 5. Purpose Match Score
    loan_purpose_lower = loan_purpose.lower() if loan_purpose else "personal"
    if loan_purpose_lower in [p.lower() for p in scheme["target_purposes"]]:
        purpose_score = 100
        explanations.append(f"Specialized for {loan_purpose} loans")
    else:
        purpose_score = 50
    scores["purpose_match"] = purpose_score
    
    # 6. Special Offers Score
    offer_count = len(scheme["special_offers"])
    offer_score = min(100, offer_count * 25)
    scores["special_offers"] = offer_score
    if offer_count >= 2:
        explanations.append(f"Includes {offer_count} special benefits")
    
    # Calculate weighted total
    total_score = sum(
        scores[factor] * weight 
        for factor, weight in SCORING_WEIGHTS.items()
    )
    
    return round(total_score, 1), explanations


def _generate_pros_cons(
    scheme: LoanScheme,
    interest_rate: float,
    emi: int,
    processing_fee: int
) -> Tuple[List[str], List[str]]:
    """Generate pros and cons for a scheme."""
    
    pros = []
    cons = []
    
    # Interest rate
    if interest_rate <= 11:
        pros.append("Low interest rate")
    elif interest_rate >= 15:
        cons.append("Higher interest rate")
    
    # Processing fee
    if processing_fee == 0:
        pros.append("Zero processing fee")
    elif processing_fee >= 5000:
        cons.append("High processing fee")
    
    # Special offers
    for offer in scheme["special_offers"][:2]:
        pros.append(offer)
    
    # Risk notes
    for note in scheme["risk_notes"][:2]:
        cons.append(note)
    
    # Bank type
    if scheme["bank_type"] == "bank":
        pros.append("Backed by RBI-regulated bank")
    
    return pros[:3], cons[:2]


def _generate_recommendations_response(
    recommendations: List[SchemeRecommendation],
    state: AgentState
) -> str:
    """Generate conversational response with recommendations."""
    
    loan_amount = state.get("loan_amount", 500000)
    credit_score = state.get("credit_score", 700)
    
    best = recommendations[0]
    
    response = (
        f"🏦 **Loan Scheme Analysis Complete!**\n\n"
        f"Based on your profile (Credit Score: {credit_score}, "
        f"Loan: ₹{loan_amount:,}), I've analyzed eligible schemes.\n\n"
        f"---\n\n"
    )
    
    # Best recommendation
    response += (
        f"🏆 **Best Match: {best.scheme['bank_name']} - {best.scheme['scheme_name']}**\n\n"
        f"| Parameter | Value |\n"
        f"|-----------|-------|\n"
        f"| Interest Rate | {best.interest_rate}% p.a. |\n"
        f"| Monthly EMI | ₹{best.emi:,} |\n"
        f"| Total Cost | ₹{best.total_cost:,} |\n"
        f"| Match Score | {best.score}/100 |\n\n"
    )
    
    # Why this scheme
    response += "**Why this scheme:**\n"
    for exp in best.explanation[:3]:
        response += f"• {exp}\n"
    response += "\n"
    
    # Pros
    if best.pros:
        response += "✅ **Pros:** " + ", ".join(best.pros[:3]) + "\n\n"
    
    # Alternatives
    if len(recommendations) > 1:
        response += "---\n\n**📋 Alternatives:**\n\n"
        
        for i, alt in enumerate(recommendations[1:3], 1):
            response += (
                f"**{i}. {alt.scheme['bank_name']} - {alt.scheme['scheme_name']}**\n"
                f"   • Rate: {alt.interest_rate}% | EMI: ₹{alt.emi:,} | Score: {alt.score}/100\n\n"
            )
    
    response += (
        "---\n\n"
        "💬 **Your Decision:**\n"
        "• Reply **'1'** to proceed with the best match\n"
        "• Reply **'2'** or **'3'** to select an alternative\n"
        "• Reply **'compare'** for detailed comparison\n"
    )
    
    return response


def _generate_no_schemes_response(state: AgentState) -> str:
    """Generate response when no schemes are eligible."""
    
    credit_score = state.get("credit_score", 0)
    loan_amount = state.get("loan_amount", 0)
    
    response = (
        f"❌ **No Eligible Schemes Found**\n\n"
        f"Unfortunately, we couldn't find any schemes matching your requirements.\n\n"
        f"**Your Profile:**\n"
        f"• Credit Score: {credit_score}\n"
        f"• Requested Amount: ₹{loan_amount:,}\n\n"
        f"**Suggestions:**\n"
    )
    
    if credit_score < 650:
        response += "• Improve your credit score to 650+ for more options\n"
    if loan_amount > 2000000:
        response += "• Consider a lower loan amount\n"
    
    response += (
        "• Check back after 3-6 months\n"
        "• Contact our support for personalized assistance\n"
    )
    
    return response


def _parse_scheme_selection(message: str, state: AgentState) -> Optional[str]:
    """Parse user's scheme selection."""
    
    message_lower = message.lower().strip()
    recommendations = state.get("scheme_recommendations", [])
    
    if not recommendations:
        return None
    
    # Check for numbered selection
    if message_lower in ["1", "one", "first", "best"]:
        return recommendations[0]["scheme_id"] if len(recommendations) > 0 else None
    elif message_lower in ["2", "two", "second"]:
        return recommendations[1]["scheme_id"] if len(recommendations) > 1 else None
    elif message_lower in ["3", "three", "third"]:
        return recommendations[2]["scheme_id"] if len(recommendations) > 2 else None
    
    return None


def _handle_scheme_selection(new_state: dict, state: AgentState, scheme_id: str) -> AgentState:
    """Handle user's scheme selection."""
    
    recommendations = state.get("scheme_recommendations", [])
    selected = None
    
    for rec in recommendations:
        if rec["scheme_id"] == scheme_id:
            selected = rec
            break
    
    if not selected:
        # Invalid selection
        response = "Please select a valid option (1, 2, or 3)."
        new_state["stage"] = ConversationStage.SCHEME_RECOMMENDATION
    else:
        # Store selected scheme
        new_state["selected_scheme"] = selected
        new_state["final_interest_rate"] = selected["interest_rate"]
        new_state["emi"] = selected["emi"]
        new_state["stage"] = ConversationStage.RATE_NEGOTIATION
        
        response = (
            f"✅ **Excellent Choice!**\n\n"
            f"You've selected **{selected['bank_name']} - {selected['scheme_name']}**\n\n"
            f"**Final Terms:**\n"
            f"• Interest Rate: {selected['interest_rate']}% p.a.\n"
            f"• Monthly EMI: ₹{selected['emi']:,}\n\n"
            f"Would you like to proceed with this rate, or would you like to **negotiate** for a better deal?\n\n"
            f"Reply **'accept'** to proceed or **'negotiate'** to request a better rate."
        )
    
    new_state["current_agent"] = AgentType.SCHEME
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    return new_state
