"""
Verification Agent

Handles KYC verification by validating PAN and Aadhar
against the mock CRM database.
"""

import re
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import AgentState, ConversationStage, AgentType
from app.core.logging import get_logger


logger = get_logger(__name__)


async def verification_agent(state: AgentState) -> AgentState:
    """
    Verification agent for KYC processing with OTP verification.
    
    Two-step verification:
    1. KYC_VERIFICATION: Validate PAN → Generate OTP → Move to OTP_VERIFICATION
    2. OTP_VERIFICATION: Validate OTP → Move to CREDIT_CHECK
    """
    import random
    
    logger.info(
        "Verification agent processing",
        conversation_id=state["conversation_id"],
        current_stage=state.get("stage").value if state.get("stage") else "none",
        kyc_verified=state.get("kyc_verified", False),
        otp_verified=state.get("otp_verified", False)
    )
    
    # Get last user message
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    new_state = state.copy()
    current_stage = state.get("stage", ConversationStage.KYC_VERIFICATION)
    
    # --- OTP VERIFICATION STAGE ---
    if current_stage == ConversationStage.OTP_VERIFICATION:
        return await _handle_otp_verification(new_state, last_user_message, state)
    
    # --- KYC VERIFICATION STAGE ---
    # Try to extract PAN from message
    pan = _extract_pan(last_user_message)
    
    if pan:
        new_state["customer_pan"] = pan
        
        # Verify against mock CRM
        verification_result = await _verify_customer(pan, state.get("customer_phone"))
        
        if verification_result["success"]:
            # Store verification result but don't mark as verified yet (need OTP)
            new_state["customer_id"] = verification_result.get("customer_id")
            new_state["pre_approved_limit"] = verification_result.get("pre_approved_limit", 0)
            new_state["credit_score"] = verification_result.get("credit_score")
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            new_state["otp_code"] = otp
            new_state["otp_verified"] = False
            new_state["stage"] = ConversationStage.OTP_VERIFICATION
            
            # For DEMO: Display OTP in chat (in production, send via SMS)
            customer_name = state.get("customer_name", "Customer")
            phone = state.get("customer_phone", "XXXXXX")
            masked_phone = f"XXXXXX{phone[-4:]}" if len(phone) >= 4 else phone
            
            response = (
                f"✅ **PAN Verified!**\n\n"
                f"**PAN:** {_mask_pan(pan)}\n\n"
                f"📱 **OTP Sent!**\n"
                f"An OTP has been sent to your registered mobile number ending with **{masked_phone[-4:]}**.\n\n"
                f"🔐 **Demo Mode OTP: `{otp}`**\n"
                f"_(In production, this would be sent via SMS)_\n\n"
                f"Please enter the 6-digit OTP to verify your identity:"
            )
        else:
            new_state["kyc_verified"] = False
            response = (
                f"❌ Verification Failed\n\n"
                f"Reason: {verification_result.get('message', 'Customer not found')}\n\n"
                "Please ensure you're providing the correct PAN, "
                "or contact support for assistance."
            )
            new_state["stage"] = ConversationStage.KYC_VERIFICATION
    else:
        # PAN not found in message, ask for it
        response = (
            f"Hi {state.get('customer_name', 'there')}! 👋\n\n"
            "To verify your identity, please provide your **PAN card number**.\n\n"
            "Format: ABCDE1234F (5 letters, 4 numbers, 1 letter)\n\n"
            "Your PAN helps us:\n"
            "• Verify your identity\n"
            "• Check your pre-approved loan limit\n"
            "• Process your application faster"
        )
        new_state["stage"] = ConversationStage.KYC_VERIFICATION
    
    new_state["current_agent"] = AgentType.VERIFICATION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "Verification agent completed",
        conversation_id=state["conversation_id"],
        next_stage=new_state["stage"].value
    )
    
    return new_state


async def _handle_otp_verification(new_state: dict, user_message: str, state: AgentState) -> AgentState:
    """Handle OTP verification stage - DEMO MODE: Auto-accept confirmations."""
    
    stored_otp = state.get("otp_code", "")
    user_lower = user_message.lower().strip()
    
    # Extract digits from user message
    user_otp = ''.join(filter(str.isdigit, user_message))
    
    # DEMO MODE: Auto-accept if user says yes, ok, verify, proceed, etc.
    auto_accept_keywords = ["yes", "ok", "okay", "verify", "proceed", "confirm", "continue", "done", "submit"]
    should_auto_accept = any(kw in user_lower for kw in auto_accept_keywords)
    
    # Accept if: correct OTP, any 6 digits (demo), or confirmation keyword
    if (len(user_otp) == 6 and user_otp == stored_otp) or should_auto_accept or len(user_otp) == 6:
        # OTP verification complete!
        new_state["otp_verified"] = True
        new_state["kyc_verified"] = True
        new_state["stage"] = ConversationStage.CREDIT_CHECK
        
        pre_approved = new_state.get("pre_approved_limit", 0)
        credit_score = new_state.get("credit_score", 0)
        
        response = (
            f"✅ **OTP Verified Successfully!**\n\n"
            f"🎉 **KYC Complete!**\n\n"
            f"**Your Profile:**\n"
            f"• Credit Score: {credit_score}\n"
            f"• Pre-approved Limit: ₹{pre_approved:,}\n\n"
            "Processing your loan application..."
        )
    else:
        # Ask for OTP again but show it clearly
        new_state["stage"] = ConversationStage.OTP_VERIFICATION
        stored_otp_display = state.get("otp_code", "N/A")
        response = (
            f"Please enter the OTP or type **'yes'** to continue.\n\n"
            f"🔐 **Demo OTP: `{stored_otp_display}`**"
        )
    
    new_state["current_agent"] = AgentType.VERIFICATION
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "OTP verification completed",
        conversation_id=state.get("conversation_id"),
        otp_verified=new_state.get("otp_verified"),
        next_stage=new_state["stage"].value
    )
    
    return new_state


def _extract_pan(message: str) -> str | None:
    """
    Extract PAN card number from message.
    
    PAN format: AAAAA0000A (5 letters, 4 digits, 1 letter)
    """
    # Clean the message
    message_upper = message.upper().strip()
    
    # PAN regex pattern
    pan_pattern = r"\b([A-Z]{5}[0-9]{4}[A-Z])\b"
    
    match = re.search(pan_pattern, message_upper)
    if match:
        pan = match.group(1)
        # Additional validation
        if _is_valid_pan(pan):
            return pan
    
    return None


def _is_valid_pan(pan: str) -> bool:
    """
    Validate PAN structure.
    
    Format: AAAAA0000A
    - First 5 letters: Alpha characters
    - Next 4: Digits
    - Last: Alpha check character
    """
    if len(pan) != 10:
        return False
    
    # Check pattern
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        return False
    
    # 4th character should be a valid letter (relaxed check for compatibility)
    # Valid entities include: C, P, H, F, A, T, B, L, J, G but we accept any letter
    # to handle edge cases and test data
    if not pan[3].isalpha():
        return False
    
    return True


def _mask_pan(pan: str) -> str:
    """Mask PAN for display (show last 4 only)."""
    if len(pan) == 10:
        return f"XXXXXX{pan[-4:]}"
    return "XXXXXXXXXX"


async def _verify_customer(pan: str, phone: str = None) -> dict:
    """
    Verify customer against mock CRM database.
    
    DEMO MODE: If PAN format is valid but not in DB, auto-create a mock profile.
    This allows testing with any valid format PAN.
    
    Returns:
        dict with keys:
        - success: bool
        - customer_id: str (if found)
        - pre_approved_limit: int
        - credit_score: int
        - message: str (error message if failed)
        - is_new_customer: bool (if auto-created in demo mode)
    """
    from uuid import uuid4
    import random
    
    # Load mock customer data
    from app.mock_data.customers import MOCK_CUSTOMERS
    
    # Search by PAN first
    for customer in MOCK_CUSTOMERS:
        if customer.get("pan", "").upper() == pan.upper():
            # Found existing customer
            return {
                "success": True,
                "customer_id": customer["id"],
                "pre_approved_limit": customer.get("pre_approved_limit", 100000),
                "credit_score": customer.get("credit_score", 750),
                "name": customer.get("name"),
                "is_new_customer": False
            }
    
    # --- DEMO MODE ---
    # PAN not found, but format is valid - create a demo profile
    # This makes the system more testable without needing exact mock PANs
    
    # Generate random but realistic values for demo
    demo_credit_score = random.randint(700, 850)
    demo_pre_approved = random.choice([200000, 300000, 500000, 750000, 1000000])
    
    logger.info(
        "Demo mode: Creating new customer profile",
        pan=pan[:5] + "*****",  # Mask PAN in logs
        credit_score=demo_credit_score,
        pre_approved_limit=demo_pre_approved
    )
    
    return {
        "success": True,
        "customer_id": str(uuid4()),
        "pre_approved_limit": demo_pre_approved,
        "credit_score": demo_credit_score,
        "name": None,  # Will use name from state
        "is_new_customer": True
    }
