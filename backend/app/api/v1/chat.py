"""
Chat API Routes

Main conversation endpoint for the agentic loan sales system.
Routes messages through the LangGraph agent orchestrator.
"""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationStage,
    AgentType,
)
from app.api.deps import DBSession, OptionalUser
from app.core.logging import get_logger
from app.services.conversation_manager import ConversationManager
from app.agents.graph import run_agent_graph


router = APIRouter()
logger = get_logger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: DBSession,
    background_tasks: BackgroundTasks,
    current_user: OptionalUser = None
):
    """
    Main chat endpoint for loan conversation.
    
    This endpoint:
    1. Receives user message
    2. Loads or creates conversation state
    3. Routes through LangGraph agent orchestrator
    4. Returns agent response with next actions
    
    The conversation flows through stages:
    GREETING → NEED_ANALYSIS → KYC_VERIFICATION → CREDIT_CHECK →
    SALARY_UPLOAD → UNDERWRITING → DECISION → SANCTION_LETTER
    """
    try:
        # Get or create conversation
        conversation_id = request.conversation_id or str(uuid4())
        
        logger.info(
            "Chat message received",
            conversation_id=conversation_id,
            message_length=len(request.message),
            has_user=current_user is not None
        )
        
        # Load conversation state
        conversation_manager = ConversationManager(db)
        state = await conversation_manager.get_or_create_state(
            conversation_id=conversation_id,
            customer_phone=request.customer_phone
        )
        
        # Add user message to state
        state = conversation_manager.add_user_message(state, request.message)
        
        # Run through agent graph
        result_state = await run_agent_graph(state, db)
        
        # Save updated state
        await conversation_manager.save_state(result_state)
        
        # Get the last assistant message
        from langchain_core.messages import AIMessage
        assistant_messages = [
            m for m in result_state["messages"] 
            if isinstance(m, AIMessage)
        ]
        
        last_message = assistant_messages[-1] if assistant_messages else None
        
        # Build response
        response = ChatResponse(
            conversation_id=conversation_id,
            message=last_message.content if last_message else "I'm here to help you with your loan application.",
            agent_type=result_state.get("current_agent") or AgentType.MASTER,
            stage=result_state["stage"],
            actions=_get_available_actions(result_state),
            metadata={
                "customer_name": result_state.get("customer_name"),
                "loan_amount": result_state.get("loan_amount"),
                "kyc_verified": result_state.get("kyc_verified"),
                "credit_score": result_state.get("credit_score"),
            },
            application_id=result_state.get("application_id"),
            requires_input=_get_required_input(result_state)
        )
        
        # Background: log audit trail
        background_tasks.add_task(
            _log_chat_audit,
            conversation_id,
            request.message,
            response.message,
            result_state.get("current_agent")
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Chat processing error",
            error=str(e),
            conversation_id=request.conversation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message. Please try again."
        )


@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    db: DBSession
):
    """
    Get conversation history for a session.
    """
    conversation_manager = ConversationManager(db)
    state = await conversation_manager.get_state(conversation_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Extract messages from LangChain format
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    messages = []
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, SystemMessage):
            role = "system"
        else:
            role = "unknown"
        
        messages.append({
            "role": role,
            "content": msg.content,
        })
    
    return {
        "conversation_id": conversation_id,
        "stage": state.get("stage").value if state.get("stage") else None,
        "messages": messages,
        "customer_name": state.get("customer_name"),
        "application_id": state.get("application_id")
    }


@router.delete("/history/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    db: DBSession
):
    """
    Clear conversation history.
    """
    conversation_manager = ConversationManager(db)
    await conversation_manager.delete_state(conversation_id)
    
    return {"message": "Conversation cleared", "conversation_id": conversation_id}


def _get_available_actions(state: dict) -> list[str]:
    """Determine available actions based on conversation stage."""
    actions = []
    stage = state.get("stage")
    
    if stage == ConversationStage.SALARY_UPLOAD:
        actions.append("upload_salary_slip")
    
    if stage == ConversationStage.DECISION:
        if state.get("decision") == "APPROVED":
            actions.append("generate_sanction_letter")
        actions.append("start_new_application")
    
    if stage == ConversationStage.SANCTION_LETTER:
        actions.append("download_sanction_letter")
    
    return actions


def _get_required_input(state: dict) -> Optional[str]:
    """Determine what input is required from user."""
    stage_inputs = {
        ConversationStage.NEED_ANALYSIS: "loan_details",
        ConversationStage.KYC_VERIFICATION: "pan_number",
        ConversationStage.SALARY_UPLOAD: "salary_slip",
    }
    
    return stage_inputs.get(state.get("stage"))


async def _log_chat_audit(
    conversation_id: str,
    user_message: str,
    agent_response: str,
    agent_type: Optional[AgentType]
):
    """Log chat interaction for audit trail."""
    logger.info(
        "Chat audit",
        conversation_id=conversation_id,
        user_message_length=len(user_message),
        response_length=len(agent_response),
        agent_type=agent_type.value if agent_type else None
    )
