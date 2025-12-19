"""
Sales Agent

Handles initial customer engagement, loan need analysis,
and information collection through natural conversation.
"""

import re
from typing import Optional, Tuple
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import AgentState, ConversationStage, AgentType
from app.services.llm_adapter import get_llm_adapter
from app.core.logging import get_logger


logger = get_logger(__name__)


SALES_SYSTEM_PROMPT = """You are a skilled personal loan sales agent for a leading financial institution.
Your goal is to understand customer needs, collect required information, and guide them toward a loan application.

Current Information Collected:
- Customer Name: {customer_name}
- Phone: {customer_phone}
- Loan Amount: ₹{loan_amount}
- Tenure: {tenure_months} months
- Purpose: {loan_purpose}

Your tasks:
1. Greet the customer warmly if this is a new conversation
2. Understand their loan requirements (amount, purpose, tenure)
3. Collect their basic details (name, phone)
4. Answer any questions about loan products
5. Build rapport and trust

Communication Guidelines:
- Use friendly, professional Indian English
- Be helpful but not pushy
- Explain loan terms in simple language
- Use ₹ for all currency amounts
- Format large numbers with commas (e.g., ₹2,00,000)

If all required information is collected, summarize and confirm before proceeding.
Always end with a clear call-to-action or question."""


async def sales_agent(state: AgentState) -> AgentState:
    """
    Sales agent for customer engagement and information collection.
    
    Now handles ALL sales-related stages including GREETING.
    Responsible for:
    - Initial greeting and welcome
    - Detecting loan interest
    - Extracting loan details (amount, tenure, purpose)
    - Collecting customer info (name, phone)
    - Advancing to KYC when ready
    """
    logger.info(
        "Sales agent processing",
        conversation_id=state["conversation_id"],
        current_stage=state.get("stage").value if state.get("stage") else "none",
        has_name=state.get("customer_name") is not None,
        has_amount=state.get("loan_amount") is not None
    )
    
    # Get last user message
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    new_state = state.copy()
    user_lower = last_user_message.lower()
    current_stage = state.get("stage", ConversationStage.GREETING)
    
    # Check if user is asking about loans
    loan_keywords = ["loan", "borrow", "credit", "money", "finance", "personal loan", 
                     "lakh", "lakhs", "amount", "emi", "interest"]
    is_loan_inquiry = any(kw in user_lower for kw in loan_keywords)
    
    # GREETING STAGE: Welcome user or detect loan interest
    if current_stage == ConversationStage.GREETING:
        if is_loan_inquiry:
            # User mentioned loan - move to need analysis and extract info
            extracted = _extract_loan_info(last_user_message, state)
            _update_state_with_extraction(new_state, extracted)
            
            # Generate response asking for loan details
            response = await _generate_sales_response(new_state, last_user_message)
            new_state["stage"] = _determine_next_stage(new_state)
        else:
            # Just a greeting - give welcome message
            response = (
                "Hello! Welcome to our Personal Loan service. 👋\n\n"
                "I'm your AI assistant and I can help you:\n"
                "• Apply for a personal loan (₹50,000 - ₹50,00,000)\n"
                "• Check your pre-approved limit\n"
                "• Calculate your EMI\n\n"
                "How can I assist you today?"
            )
            new_state["stage"] = ConversationStage.GREETING
    
    # NEED_ANALYSIS & COLLECTING_DETAILS: Extract info and advance
    else:
        # Extract information from user message
        extracted = _extract_loan_info(last_user_message, state)
        _update_state_with_extraction(new_state, extracted)
        
        # Generate application ID if transitioning to KYC and no ID exists
        # This happens when all basic info (name, phone, amount) is collected
        next_stage = _determine_next_stage(new_state)
        if next_stage == ConversationStage.KYC_VERIFICATION and not new_state.get("application_id"):
            from uuid import uuid4
            from datetime import datetime
            
            app_id = f"LOAN-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
            new_state["application_id"] = app_id
            
            logger.info(
                "Generated application ID",
                conversation_id=state["conversation_id"],
                application_id=app_id,
                customer_name=new_state.get("customer_name")
            )
        
        # Generate response based on what's collected (async LLM call with fallback)
        response = await _generate_sales_response(new_state, last_user_message)
        
        # Determine next stage based on collected info
        new_state["stage"] = next_stage
    
    new_state["current_agent"] = AgentType.SALES
    new_state["messages"] = state["messages"] + [AIMessage(content=response)]
    
    logger.info(
        "Sales agent completed",
        conversation_id=state["conversation_id"],
        next_stage=new_state["stage"].value,
        collected_name=new_state.get("customer_name"),
        collected_amount=new_state.get("loan_amount")
    )
    
    return new_state


def _update_state_with_extraction(state: dict, extracted: dict) -> None:
    """Update state with extracted information."""
    if extracted["name"]:
        state["customer_name"] = extracted["name"]
    if extracted["phone"]:
        state["customer_phone"] = extracted["phone"]
    if extracted["amount"]:
        state["loan_amount"] = extracted["amount"]
    if extracted["tenure"]:
        state["tenure_months"] = extracted["tenure"]
    if extracted["purpose"]:
        state["loan_purpose"] = extracted["purpose"]


def _extract_loan_info(message: str, state: AgentState) -> dict:
    """
    Extract loan-related information from user message.
    
    Uses regex patterns and NLP-style matching.
    """
    extracted = {
        "name": None,
        "phone": None,
        "amount": None,
        "tenure": None,
        "purpose": None
    }
    
    message_lower = message.lower()
    
    # Extract loan amount
    # Patterns: "2 lakh", "2,00,000", "200000", "₹2L", "2L"
    amount_patterns = [
        r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*)\s*(?:lakh|lac|l)\b",  # X lakh
        r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*)\s*(?:crore|cr)\b",    # X crore  
        r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})*(?:,\d{3})?)\b",  # X,XX,XXX format
        r"(?:₹|rs\.?|inr)?\s*(\d{5,8})\b",  # Plain number 100000+
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, message_lower)
        if match:
            amount_str = match.group(1).replace(",", "")
            amount = int(amount_str)
            
            # Handle lakh/crore multipliers
            if "lakh" in message_lower or "lac" in message_lower:
                if amount < 100:  # "2 lakh" not "200000 lakh"
                    amount *= 100000
            elif "crore" in message_lower or " cr" in message_lower:
                if amount < 100:
                    amount *= 10000000
            
            # Validate range (10K to 1Cr)
            if 10000 <= amount <= 10000000:
                extracted["amount"] = amount
                break
    
    # Extract tenure
    # Patterns: "12 months", "2 years", "24 month", "1 year"
    tenure_patterns = [
        (r"(\d+)\s*(?:month|months|mo)\b", 1),  # X months
        (r"(\d+)\s*(?:year|years|yr|yrs)\b", 12),  # X years -> months
    ]
    
    for pattern, multiplier in tenure_patterns:
        match = re.search(pattern, message_lower)
        if match:
            tenure = int(match.group(1)) * multiplier
            if 6 <= tenure <= 84:  # Valid tenure range
                extracted["tenure"] = tenure
                break
    
    # Extract phone number
    phone_pattern = r"\b([6-9]\d{9})\b"
    phone_match = re.search(phone_pattern, message)
    if phone_match:
        extracted["phone"] = phone_match.group(1)
    
    # Extract name (heuristic: look for "I am X" or "my name is X")
    name_patterns = [
        r"(?:i am|i'm|my name is|this is|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:name|naam)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if 2 <= len(name) <= 50:
                extracted["name"] = name.title()
                break
    
    # If no name extracted yet, check if message looks like a direct name response
    # (2-3 capitalized words, no numbers, short message)
    if not extracted["name"] and not state.get("customer_name"):
        # Check if this looks like a name: starts with capital, 2-3 words, no digits
        direct_name_pattern = r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})$"
        match = re.match(direct_name_pattern, message.strip())
        if match:
            potential_name = match.group(1).strip()
            # Basic validation: 2-50 chars, no common non-name words
            non_name_words = ["yes", "no", "ok", "okay", "hi", "hello", "thanks", "thank"]
            if 2 <= len(potential_name) <= 50 and potential_name.lower() not in non_name_words:
                extracted["name"] = potential_name.title()
    
    # Extract purpose (keyword matching)
    purpose_keywords = {
        "medical": ["medical", "hospital", "health", "treatment", "surgery"],
        "education": ["education", "study", "college", "university", "course", "degree"],
        "wedding": ["wedding", "marriage", "shaadi"],
        "home renovation": ["renovation", "home improvement", "repair", "construction"],
        "travel": ["travel", "vacation", "holiday", "trip"],
        "debt consolidation": ["debt", "consolidation", "pay off", "clear loan"],
        "personal expenses": ["personal", "expenses", "emergency"],
        "business": ["business", "startup", "venture"],
    }
    
    for purpose, keywords in purpose_keywords.items():
        if any(kw in message_lower for kw in keywords):
            extracted["purpose"] = purpose
            break
    
    return extracted


async def _generate_sales_response(state: AgentState, user_message: str) -> str:
    """Generate sales response using LLM with context awareness."""
    
    has_name = state.get("customer_name")
    has_phone = state.get("customer_phone")
    has_amount = state.get("loan_amount")
    has_tenure = state.get("tenure_months")
    has_purpose = state.get("loan_purpose")
    
    # Build context for LLM
    context_parts = []
    if has_name:
        context_parts.append(f"Customer Name: {has_name}")
    if has_phone:
        context_parts.append(f"Phone: {has_phone}")
    if has_amount:
        context_parts.append(f"Loan Amount: ₹{has_amount:,}")
    if has_tenure:
        context_parts.append(f"Tenure: {has_tenure} months")
    if has_purpose:
        context_parts.append(f"Purpose: {has_purpose}")
    
    collected_info = "\n".join(context_parts) if context_parts else "No information collected yet"
    
    # Determine what's still needed
    missing = []
    if not has_amount:
        missing.append("loan amount")
    if not has_tenure:
        missing.append("loan tenure")
    if not has_name:
        missing.append("customer name")
    if not has_phone:
        missing.append("mobile number")
    
    missing_info = ", ".join(missing) if missing else "All basic info collected - ready for KYC"
    
    system_prompt = f"""You are a friendly personal loan sales agent for a leading Indian financial institution.

COLLECTED CUSTOMER INFORMATION:
{collected_info}

STILL NEEDED: {missing_info}

YOUR TASK:
- If loan amount is missing: Ask about loan requirements (amount, purpose, tenure)
- If amount is there but tenure is missing: Ask about preferred tenure (6-84 months)
- If amount and tenure are there but name is missing: Ask for full name as per PAN card
- If name is there but phone is missing: Ask for 10-digit mobile number
- If all info is collected: Summarize and ask for confirmation to proceed to KYC

GUIDELINES:
- Be warm, professional, and conversational
- Use Indian English and ₹ for currency
- Format amounts with Indian number system (lakhs, crores)
- Keep responses concise (2-4 sentences max)
- Always end with a clear question or call-to-action
- Use appropriate emojis sparingly (🙏, 👍, 💰)

Respond naturally to: "{user_message}"
"""

    try:
        llm = get_llm_adapter()
        response = await llm.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.content
        
    except Exception as e:
        logger.warning(f"LLM call failed, using fallback: {e}")
        return _generate_fallback_response(state, user_message)


def _generate_fallback_response(state: AgentState, user_message: str) -> str:
    """Fallback hardcoded response if LLM fails."""
    
    has_name = state.get("customer_name")
    has_phone = state.get("customer_phone")
    has_amount = state.get("loan_amount")
    has_tenure = state.get("tenure_months")
    has_purpose = state.get("loan_purpose")
    
    # Check if all info collected first (highest priority)
    if has_name and has_phone and has_amount:
        return (
            f"Excellent! Here's your loan summary:\n"
            f"👤 Name: {has_name}\n"
            f"📱 Mobile: {has_phone}\n"
            f"💰 Amount: ₹{has_amount:,}\n"
            f"📅 Tenure: {has_tenure or 12} months\n"
            f"📋 Purpose: {has_purpose or 'Personal'}\n\n"
            "Shall I proceed with KYC verification? Please confirm with 'yes' or share your PAN card number."
        )
    
    # Missing phone (name collected)
    if has_name and has_amount and not has_phone:
        return f"Thank you, {has_name}! 🙏 Could you share your 10-digit mobile number?"
    
    # Missing name (amount and tenure collected)
    if has_amount and not has_name:
        if has_tenure:
            return f"Perfect! ₹{has_amount:,} for {has_tenure} months. May I know your full name as per PAN card?"
        else:
            return f"Great! You're looking for ₹{has_amount:,}. What tenure would you prefer (6-84 months)?"
    
    # Missing tenure (only amount collected)
    if has_amount and not has_tenure:
        return f"Great! You're looking for ₹{has_amount:,}. What tenure would you prefer (6-84 months)?"
    
    # Nothing collected yet
    return (
        "I'd be happy to help you with a personal loan! 💰\n\n"
        "Could you please tell me:\n"
        "1. How much would you like to borrow?\n"
        "2. For what purpose?\n"
        "3. What tenure would you prefer (6-84 months)?"
    )


def _determine_next_stage(state: AgentState) -> ConversationStage:
    """Determine next stage based on collected information."""
    
    has_name = state.get("customer_name")
    has_phone = state.get("customer_phone")
    has_amount = state.get("loan_amount")
    
    # If all basic info collected, move to KYC
    if has_name and has_phone and has_amount:
        return ConversationStage.KYC_VERIFICATION
    
    # Still collecting
    if has_amount:
        return ConversationStage.COLLECTING_DETAILS
    
    return ConversationStage.NEED_ANALYSIS
