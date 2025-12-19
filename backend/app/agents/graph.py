"""
LangGraph Workflow

Defines the agent state graph and execution flow.
Implements the state machine for loan processing.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState, ConversationStage, create_initial_state
from app.agents.master_agent import master_agent
from app.agents.sales_agent import sales_agent
from app.agents.verification_agent import verification_agent
from app.agents.underwriting_agent import underwriting_agent
from app.agents.scheme_agent import scheme_agent
from app.agents.negotiation_agent import negotiation_agent
from app.agents.sanction_agent import sanction_agent
from app.core.logging import get_logger


logger = get_logger(__name__)


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph workflow for loan processing.
    
    Graph structure:
    
    START
      │
      ▼
    ┌─────────────┐
    │   MASTER    │◄─────────────────────────────┐
    │   AGENT     │                              │
    └──────┬──────┘                              │
           │                                      │
           ▼ (route based on stage)              │
    ┌──────┴──────┬──────────────┬──────────┬────────────┐
    │             │              │          │            │
    ▼             ▼              ▼          ▼            ▼
    SALES    VERIFICATION   UNDERWRITING  NEGOTIATION  SANCTION
    AGENT       AGENT          AGENT        AGENT       AGENT
    │             │              │          │            │
    └─────────────┴──────────────┴──────────┴────────────┘
                        │
                        ▼
                       END
    """
    
    # Create graph with AgentState
    graph = StateGraph(AgentState)
    
    # Add all agent nodes
    graph.add_node("master", master_agent)
    graph.add_node("sales", sales_agent)
    graph.add_node("verification", verification_agent)
    graph.add_node("underwriting", underwriting_agent)
    graph.add_node("scheme", scheme_agent)
    graph.add_node("negotiation", negotiation_agent)
    graph.add_node("sanction", sanction_agent)
    
    # Set entry point
    graph.set_entry_point("master")
    
    # Add conditional routing from master
    graph.add_conditional_edges(
        "master",
        _route_from_master,
        {
            "sales": "sales",
            "verification": "verification",
            "underwriting": "underwriting",
            "scheme": "scheme",
            "negotiation": "negotiation",
            "sanction": "sanction",
            "end": END,
        }
    )
    
    # All worker agents route back based on their state
    graph.add_conditional_edges(
        "sales",
        _should_continue,
        {"continue": "master", "end": END}
    )
    
    graph.add_conditional_edges(
        "verification",
        _should_continue,
        {"continue": "master", "end": END}
    )
    
    graph.add_conditional_edges(
        "underwriting",
        _should_continue,
        {"continue": "master", "end": END}
    )
    
    graph.add_conditional_edges(
        "scheme",
        _should_continue,
        {"continue": "master", "end": END}
    )
    
    graph.add_conditional_edges(
        "negotiation",
        _should_continue,
        {"continue": "master", "end": END}
    )
    
    graph.add_conditional_edges(
        "sanction",
        _should_continue,
        {"continue": "master", "end": END}
    )
    
    return graph


def _route_from_master(state: AgentState) -> Literal["sales", "verification", "underwriting", "scheme", "negotiation", "sanction", "end"]:
    """
    Determine which agent to route to from master.
    
    Based on conversation stage.
    """
    stage = state.get("stage", ConversationStage.GREETING)
    
    logger.debug(
        "Routing from master",
        stage=stage.value if hasattr(stage, 'value') else str(stage),
        conversation_id=state.get("conversation_id")
    )
    
    # Greeting and need analysis -> Sales
    if stage in [
        ConversationStage.GREETING,
        ConversationStage.NEED_ANALYSIS,
        ConversationStage.COLLECTING_DETAILS
    ]:
        return "sales"
    
    # KYC verification and OTP verification -> Verification
    elif stage in [ConversationStage.KYC_VERIFICATION, ConversationStage.OTP_VERIFICATION]:
        return "verification"
    
    # Credit check, salary, underwriting, decision -> Underwriting
    elif stage in [
        ConversationStage.CREDIT_CHECK,
        ConversationStage.SALARY_UPLOAD,
        ConversationStage.UNDERWRITING,
        ConversationStage.DECISION
    ]:
        # After approval decision, route to scheme agent for comparison
        if state.get("decision") == "APPROVED" and stage == ConversationStage.DECISION:
            return "scheme"
        return "underwriting"
    
    # Scheme recommendation -> Scheme agent
    elif stage == ConversationStage.SCHEME_RECOMMENDATION:
        return "scheme"
    
    # Rate negotiation -> Negotiation agent
    elif stage == ConversationStage.RATE_NEGOTIATION:
        return "negotiation"
    
    # Sanction letter -> Sanction
    elif stage == ConversationStage.SANCTION_LETTER:
        return "sanction"
    
    # Terminal states
    elif stage in [
        ConversationStage.COMPLETED,
        ConversationStage.REJECTED,
        ConversationStage.ERROR
    ]:
        return "end"
    
    return "end"


def _should_continue(state: AgentState) -> Literal["continue", "end"]:
    """
    Determine if agents should continue or end.
    
    For now, always end after a child agent processes.
    This prevents infinite loops - each user message gets one response.
    The next user message will trigger a new graph invocation.
    """
    # Always end after processing - one turn = one response
    # The master already processed and routed to a child agent,
    # and the child agent has now responded. Stop here.
    return "end"


# Compile the graph
_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = create_agent_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


async def run_agent_graph(
    state: AgentState,
    db: AsyncSession = None
) -> AgentState:
    """
    Execute the agent graph with given state.
    
    Args:
        state: Current conversation state
        db: Database session for persistence
    
    Returns:
        Updated state after graph execution
    """
    logger.info(
        "Running agent graph",
        conversation_id=state.get("conversation_id"),
        initial_stage=state.get("stage").value if state.get("stage") else "none"
    )
    
    graph = get_compiled_graph()
    
    # Run the graph
    try:
        # Execute graph - it will run until hitting END
        final_state = await graph.ainvoke(state)
        
        logger.info(
            "Agent graph completed",
            conversation_id=state.get("conversation_id"),
            final_stage=final_state.get("stage").value if final_state.get("stage") else "none"
        )
        
        return final_state
        
    except Exception as e:
        logger.error(
            "Agent graph error",
            error=str(e),
            conversation_id=state.get("conversation_id")
        )
        
        # Return error state
        error_state = state.copy()
        error_state["stage"] = ConversationStage.ERROR
        error_state["error"] = str(e)
        
        return error_state
