"""
Master Agent

Central orchestrator that manages conversation flow and delegates to worker agents.
Implements routing logic based on conversation state.
"""

from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.state import AgentState, ConversationStage, AgentType
from app.services.llm_adapter import get_llm_adapter
from app.core.logging import get_logger


logger = get_logger(__name__)


async def master_agent(state: AgentState) -> AgentState:
    """
    Master agent that orchestrates the conversation flow.
    
    REDESIGNED: Now acts as a PURE ROUTER.
    - Does NOT generate responses
    - Does NOT add messages to state
    - Only logs and passes state through
    
    All responses come from worker agents (sales, verification, etc.)
    The routing decision happens in _route_from_master in graph.py.
    """
    logger.info(
        "Master agent routing",
        conversation_id=state["conversation_id"],
        current_stage=state["stage"].value if state["stage"] else "none"
    )
    
    # Master is now a pure router - just pass state through unchanged
    # The conditional edges in graph.py handle routing based on state["stage"]
    # Worker agents are responsible for:
    #   1. Processing user message
    #   2. Updating state (including stage transitions)
    #   3. Generating response messages
    
    return state
