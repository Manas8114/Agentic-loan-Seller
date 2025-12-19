"""
Sanction Letter Agent

Generates professional PDF sanction letters for approved loans.
"""

from datetime import datetime
from uuid import uuid4
from langchain_core.messages import AIMessage

from app.agents.state import AgentState, ConversationStage, AgentType
from app.core.logging import get_logger


logger = get_logger(__name__)


async def sanction_agent(state: AgentState) -> AgentState:
    """
    Sanction letter generation agent.
    
    Creates a professional PDF sanction letter with:
    - Customer details
    - Loan terms
    - EMI schedule
    - Terms and conditions
    - Digital signature
    """
    logger.info(
        "Sanction agent processing",
        conversation_id=state["conversation_id"],
        application_id=state.get("application_id"),
        approved_amount=state.get("approved_amount")
    )
    
    new_state = state.copy()
    
    # Verify loan is approved
    if state.get("decision") != "APPROVED":
        new_state["stage"] = ConversationStage.ERROR
        new_state["error"] = "Cannot generate sanction letter for non-approved loan"
        response = "❌ Unable to generate sanction letter. Loan must be approved first."
        new_state["messages"] = state["messages"] + [AIMessage(content=response)]
        return new_state
    
    try:
        # Generate sanction letter
        sanction_data = await _generate_sanction_letter(state)
        
        new_state["sanction_id"] = sanction_data["sanction_id"]
        new_state["sanction_letter_url"] = sanction_data["download_url"]
        new_state["stage"] = ConversationStage.COMPLETED
        
        response = (
            f"📄 **Sanction Letter Generated!**\n\n"
            f"**Sanction ID:** {sanction_data['sanction_id']}\n"
            f"**Date:** {datetime.now().strftime('%d %B %Y')}\n\n"
            f"**Loan Summary:**\n"
            f"• Borrower: {state.get('customer_name')}\n"
            f"• Sanctioned Amount: ₹{state.get('approved_amount'):,}\n"
            f"• Interest Rate: {state.get('interest_rate')}% p.a.\n"
            f"• EMI: ₹{state.get('emi'):,}/month\n"
            f"• Tenure: {state.get('tenure_months')} months\n\n"
            f"📥 [Download Sanction Letter]({sanction_data['download_url']})\n\n"
            f"---\n\n"
            f"✅ **Next Steps:**\n"
            f"1. Review and sign the sanction letter\n"
            f"2. Submit any pending documents\n"
            f"3. Complete e-Mandate for EMI deduction\n"
            f"4. Receive disbursement within 24-48 hours\n\n"
            f"A loan officer will contact you shortly to complete the process.\n"
            f"Thank you for choosing us! 🙏"
        )
        
    except Exception as e:
        logger.error(
            "Sanction letter generation failed",
            error=str(e),
            conversation_id=state["conversation_id"]
        )
        new_state["stage"] = ConversationStage.ERROR
        new_state["error"] = str(e)
        response = (
            f"❌ Error generating sanction letter.\n\n"
            f"Please try again or contact support.\n"
            f"Reference: {state.get('conversation_id')}"
        )
    
    new_state["current_agent"] = AgentType.SANCTION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    return new_state


async def _generate_sanction_letter(state: AgentState) -> dict:
    """
    Generate sanction letter data and PDF.
    
    Returns dict with sanction_id and download_url.
    """
    # Generate unique sanction ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    sanction_id = f"SL{timestamp}{str(uuid4())[:6].upper()}"
    
    # Prepare sanction data
    sanction_data = {
        "sanction_id": sanction_id,
        "generated_at": datetime.now().isoformat(),
        "customer": {
            "name": state.get("customer_name", ""),
            "pan_masked": f"XXXXXX{state.get('customer_pan', 'XXXX')[-4:]}" if state.get("customer_pan") else "XXXXXXXXXX",
            "phone": state.get("customer_phone", ""),
            "email": state.get("customer_email", ""),
        },
        "loan": {
            "amount": state.get("approved_amount", 0),
            "tenure_months": state.get("tenure_months", 12),
            "interest_rate": state.get("interest_rate", 0),
            "emi": state.get("emi", 0),
            "purpose": state.get("loan_purpose", "Personal"),
            "processing_fee": int(state.get("approved_amount", 0) * 0.02),  # 2% processing fee
        },
        "application": {
            "id": state.get("application_id", ""),
            "conversation_id": state.get("conversation_id", ""),
        }
    }
    
    # In production, this would generate actual PDF and upload to S3
    # For now, return a mock URL
    download_url = f"/api/v1/sanction/download/{sanction_id}"
    
    # Log audit trail
    logger.info(
        "Sanction letter created",
        sanction_id=sanction_id,
        customer_name=state.get("customer_name"),
        amount=state.get("approved_amount")
    )
    
    return {
        "sanction_id": sanction_id,
        "download_url": download_url,
        "data": sanction_data
    }
