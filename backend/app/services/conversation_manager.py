"""
Conversation Manager Service

Manages conversation state persistence using Redis.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ConversationState, ChatMessage, MessageRole, ConversationStage, AgentType
from app.agents.state import AgentState, create_initial_state
from app.core.logging import get_logger


logger = get_logger(__name__)


# In-memory conversation store (replace with Redis in production)
_conversation_store: dict[str, dict] = {}


class ConversationManager:
    """
    Manages conversation state for chat sessions.
    
    In production, this would use Redis for persistence.
    Currently uses in-memory storage for simplicity.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_state(
        self,
        conversation_id: str,
        customer_phone: Optional[str] = None
    ) -> AgentState:
        """
        Get existing conversation or create new one.
        """
        # Check if conversation exists
        existing = await self.get_state(conversation_id)
        
        if existing:
            return existing
        
        # Create new state
        state = create_initial_state(conversation_id)
        
        if customer_phone:
            state["customer_phone"] = customer_phone
            
            # Try to find customer by phone
            from app.services.kyc_service import KYCService
            kyc_service = KYCService(self.db)
            customer = await kyc_service.find_by_phone(customer_phone)
            
            if customer:
                state["customer_id"] = str(customer.id)
                state["customer_name"] = customer.name
                state["kyc_verified"] = customer.kyc_verified
                state["pre_approved_limit"] = customer.pre_approved_limit
        
        # Save initial state
        await self.save_state(state)
        
        return state
    
    async def get_state(self, conversation_id: str) -> Optional[AgentState]:
        """Get conversation state by ID."""
        stored = _conversation_store.get(conversation_id)
        
        if not stored:
            return None
        
        # Reconstruct AgentState from stored data
        return self._deserialize_state(stored)
    
    async def save_state(self, state: AgentState) -> None:
        """Save conversation state."""
        conversation_id = state.get("conversation_id")
        
        if not conversation_id:
            logger.error("Cannot save state without conversation_id")
            return
        
        # Serialize state for storage
        serialized = self._serialize_state(state)
        _conversation_store[conversation_id] = serialized
        
        logger.debug(
            "Saved conversation state",
            conversation_id=conversation_id,
            stage=state.get("stage").value if state.get("stage") else None
        )
    
    async def delete_state(self, conversation_id: str) -> None:
        """Delete conversation state."""
        if conversation_id in _conversation_store:
            del _conversation_store[conversation_id]
            logger.info("Deleted conversation", conversation_id=conversation_id)
    
    def add_user_message(self, state: AgentState, content: str) -> AgentState:
        """Add a user message to state."""
        from langchain_core.messages import HumanMessage
        
        new_state = state.copy()
        new_state["messages"] = list(state.get("messages", [])) + [
            HumanMessage(content=content)
        ]
        new_state["updated_at"] = datetime.utcnow().isoformat()
        
        return new_state
    
    def _serialize_state(self, state: AgentState) -> dict:
        """Serialize state for storage."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        serialized = {}
        
        for key, value in state.items():
            if key == "messages":
                # Serialize messages
                serialized["messages"] = [
                    {
                        "type": type(msg).__name__,
                        "content": msg.content
                    }
                    for msg in value
                ]
            elif key == "stage" and value:
                serialized["stage"] = value.value if hasattr(value, 'value') else str(value)
            elif key == "current_agent" and value:
                serialized["current_agent"] = value.value if hasattr(value, 'value') else str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        
        return serialized
    
    def _deserialize_state(self, data: dict) -> AgentState:
        """Deserialize state from storage."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        from app.agents.state import ConversationStage, AgentType
        
        state = {}
        
        for key, value in data.items():
            if key == "messages":
                # Deserialize messages
                messages = []
                for msg in value:
                    msg_type = msg.get("type", "HumanMessage")
                    content = msg.get("content", "")
                    
                    if msg_type == "HumanMessage":
                        messages.append(HumanMessage(content=content))
                    elif msg_type == "AIMessage":
                        messages.append(AIMessage(content=content))
                    elif msg_type == "SystemMessage":
                        messages.append(SystemMessage(content=content))
                
                state["messages"] = messages
            elif key == "stage":
                try:
                    state["stage"] = ConversationStage(value)
                except ValueError:
                    state["stage"] = ConversationStage.GREETING
            elif key == "current_agent":
                try:
                    state["current_agent"] = AgentType(value) if value else None
                except ValueError:
                    state["current_agent"] = None
            else:
                state[key] = value
        
        return state
