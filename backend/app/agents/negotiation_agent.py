"""
Negotiation Agent

Handles interest rate negotiation after loan approval.
Allows customers to request better rates based on their credit profile.
"""

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import AgentState, ConversationStage, AgentType
from app.core.logging import get_logger


logger = get_logger(__name__)


# Maximum negotiation attempts allowed
MAX_NEGOTIATION_ATTEMPTS = 2


async def negotiation_agent(state: AgentState) -> AgentState:
    """
    Negotiation agent for interest rate discussion.
    
    Handles:
    1. Initial offer presentation after approval
    2. User requests for better rate (max 2 attempts)
    3. Accept/reject negotiation
    
    Rate reduction logic:
    - Credit score 800+: Up to 0.5% reduction per attempt
    - Credit score 750-799: Up to 0.35% reduction per attempt
    - Credit score 700-749: Up to 0.25% reduction per attempt
    """
    logger.info(
        "Negotiation agent processing",
        conversation_id=state["conversation_id"],
        current_stage=state.get("stage").value if state.get("stage") else "none",
        negotiation_attempts=state.get("rate_negotiation_attempts", 0)
    )
    
    # Get last user message
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    new_state = state.copy()
    current_stage = state.get("stage", ConversationStage.DECISION)
    attempts = state.get("rate_negotiation_attempts", 0)
    
    # Initial offer presentation (coming from DECISION stage)
    if current_stage == ConversationStage.DECISION:
        return _present_initial_offer(new_state, state)
    
    # Handle negotiation responses
    user_lower = last_user_message.lower()
    
    # Check for acceptance
    accept_keywords = ["accept", "agree", "ok", "okay", "yes", "proceed", "confirm", "fine", "good"]
    if any(kw in user_lower for kw in accept_keywords):
        return _accept_offer(new_state, state)
    
    # Check for negotiation request
    negotiate_keywords = ["better", "lower", "reduce", "discount", "negotiate", "less", "cheaper"]
    if any(kw in user_lower for kw in negotiate_keywords):
        if attempts < MAX_NEGOTIATION_ATTEMPTS:
            return _negotiate_rate(new_state, state, attempts)
        else:
            return _max_attempts_reached(new_state, state)
    
    # Default: Ask for clarification
    return _ask_for_decision(new_state, state, attempts)


def _present_initial_offer(new_state: dict, state: AgentState) -> AgentState:
    """Present the initial loan offer after approval."""
    
    # Defensive None checks with defaults
    approved_amount = state.get("approved_amount") or 0
    interest_rate = state.get("interest_rate") or 12.0
    emi = state.get("emi") or 0
    tenure = state.get("tenure_months") or 12
    credit_score = state.get("credit_score") or 700
    
    # Set initial rate as the starting point
    new_state["final_interest_rate"] = interest_rate
    new_state["rate_negotiation_attempts"] = 0
    new_state["stage"] = ConversationStage.RATE_NEGOTIATION
    
    response = (
        f"🎉 **Congratulations! Your Loan is Approved!**\n\n"
        f"**Loan Offer Details:**\n"
        f"• Approved Amount: ₹{approved_amount:,}\n"
        f"• Interest Rate: **{interest_rate}% p.a.**\n"
        f"• EMI: ₹{emi:,}/month\n"
        f"• Tenure: {tenure} months\n"
        f"• Total Repayment: ₹{emi * tenure:,}\n\n"
        f"---\n\n"
        f"💡 **Your Options:**\n"
        f"1. **Accept** this offer and proceed to sanction letter\n"
        f"2. **Negotiate** for a better interest rate\n\n"
        f"What would you like to do? (Reply with 'accept' or 'negotiate')"
    )
    
    new_state["current_agent"] = AgentType.NEGOTIATION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "Initial offer presented",
        conversation_id=state.get("conversation_id"),
        interest_rate=interest_rate
    )
    
    return new_state


def _negotiate_rate(new_state: dict, state: AgentState, attempts: int) -> AgentState:
    """Handle rate negotiation request."""
    
    # Defensive None checks with defaults
    current_rate = state.get("final_interest_rate") or state.get("interest_rate") or 12.0
    credit_score = state.get("credit_score") or 700
    approved_amount = state.get("approved_amount") or 0
    tenure = state.get("tenure_months") or 12
    
    # Calculate rate reduction based on credit score
    if credit_score >= 800:
        reduction = 0.5
    elif credit_score >= 750:
        reduction = 0.35
    else:
        reduction = 0.25
    
    new_rate = round(current_rate - reduction, 2)
    new_rate = max(new_rate, 8.0)  # Minimum rate floor
    
    # Recalculate EMI
    new_emi = _calculate_emi(approved_amount, new_rate, tenure)
    
    # Update state
    new_state["final_interest_rate"] = new_rate
    new_state["rate_negotiation_attempts"] = attempts + 1
    new_state["emi"] = new_emi
    new_state["stage"] = ConversationStage.RATE_NEGOTIATION
    
    remaining_attempts = MAX_NEGOTIATION_ATTEMPTS - (attempts + 1)
    
    # Defensive check for old EMI
    old_emi = state.get("emi") or new_emi
    
    response = (
        f"🤝 **Great news! We've reduced your rate!**\n\n"
        f"**Updated Offer:**\n"
        f"• Interest Rate: ~~{current_rate}%~~ → **{new_rate}% p.a.**\n"
        f"• New EMI: ₹{new_emi:,}/month\n"
        f"• Savings: ₹{(old_emi - new_emi) * tenure:,} over the loan term\n\n"
    )
    
    if remaining_attempts > 0:
        response += (
            f"💡 You have **{remaining_attempts}** more negotiation attempt(s).\n\n"
            f"Would you like to:\n"
            f"• **Accept** this rate\n"
            f"• **Negotiate** further\n"
        )
    else:
        response += (
            f"ℹ️ This is our **best offer** based on your profile.\n\n"
            f"Reply with **'accept'** to proceed with sanction letter."
        )
    
    new_state["current_agent"] = AgentType.NEGOTIATION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "Rate negotiated",
        conversation_id=state.get("conversation_id"),
        old_rate=current_rate,
        new_rate=new_rate,
        attempts=attempts + 1
    )
    
    return new_state


def _accept_offer(new_state: dict, state: AgentState) -> AgentState:
    """Accept the current offer and proceed to sanction letter."""
    
    final_rate = state.get("final_interest_rate") or state.get("interest_rate", 12.0)
    approved_amount = state.get("approved_amount", 0)
    emi = state.get("emi", 0)
    tenure = state.get("tenure_months", 12)
    
    new_state["final_interest_rate"] = final_rate
    new_state["stage"] = ConversationStage.SANCTION_LETTER
    
    response = (
        f"✅ **Offer Accepted!**\n\n"
        f"**Final Loan Terms:**\n"
        f"• Amount: ₹{approved_amount:,}\n"
        f"• Interest Rate: {final_rate}% p.a.\n"
        f"• EMI: ₹{emi:,}/month\n"
        f"• Tenure: {tenure} months\n\n"
        f"📄 Generating your sanction letter now..."
    )
    
    new_state["current_agent"] = AgentType.NEGOTIATION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "Offer accepted",
        conversation_id=state.get("conversation_id"),
        final_rate=final_rate
    )
    
    return new_state


def _max_attempts_reached(new_state: dict, state: AgentState) -> AgentState:
    """Inform user max negotiation attempts reached."""
    
    final_rate = state.get("final_interest_rate") or state.get("interest_rate", 12.0)
    
    new_state["stage"] = ConversationStage.RATE_NEGOTIATION
    
    response = (
        f"ℹ️ **Maximum Negotiation Attempts Reached**\n\n"
        f"You've used all {MAX_NEGOTIATION_ATTEMPTS} negotiation attempts.\n"
        f"Your current rate of **{final_rate}%** is our best offer.\n\n"
        f"Please reply with **'accept'** to proceed with the sanction letter."
    )
    
    new_state["current_agent"] = AgentType.NEGOTIATION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    return new_state


def _ask_for_decision(new_state: dict, state: AgentState, attempts: int) -> AgentState:
    """Ask user to make a decision."""
    
    final_rate = state.get("final_interest_rate") or state.get("interest_rate", 12.0)
    remaining = MAX_NEGOTIATION_ATTEMPTS - attempts
    
    new_state["stage"] = ConversationStage.RATE_NEGOTIATION
    
    response = (
        f"I didn't quite understand. Your current offer is at **{final_rate}% p.a.**\n\n"
        f"Please choose:\n"
        f"• Reply **'accept'** to proceed\n"
    )
    
    if remaining > 0:
        response += f"• Reply **'negotiate'** to request a better rate ({remaining} attempt(s) left)\n"
    
    new_state["current_agent"] = AgentType.NEGOTIATION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    return new_state
