"""
LLM Adapter

Provides LLM-agnostic interface for Claude, OpenAI, and other providers.
Uses factory pattern for easy provider switching.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any] = None


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters."""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def get_chat_model(self) -> BaseChatModel:
        """Get the underlying LangChain chat model."""
        pass
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """Convert dict messages to LangChain format."""
        lc_messages = []
        
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
        
        return lc_messages


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic Claude models."""
    
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.anthropic_api_key
        
        if not self.api_key:
            logger.warning("Anthropic API key not configured")
        
        self._chat_model = ChatAnthropic(
            model=self.model,
            anthropic_api_key=self.api_key,
            timeout=30,
            max_retries=2,
        )
    
    def get_chat_model(self) -> BaseChatModel:
        return self._chat_model
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Claude."""
        
        # Convert to LangChain message format
        lc_messages = self._convert_messages(messages)
        
        try:
            response = await self._chat_model.ainvoke(
                lc_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return LLMResponse(
                content=response.content,
                model=self.model,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if hasattr(response, 'usage_metadata') else 0,
                finish_reason="stop",
                metadata={"provider": "anthropic"}
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class OpenAIAdapter(LLMAdapter):
    """Adapter for OpenAI GPT models."""
    
    def __init__(self, model: str = "gpt-4o", api_key: str = None):
        self.model = model
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
        
        self._chat_model = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            timeout=30,
            max_retries=2,
        )
    
    def get_chat_model(self) -> BaseChatModel:
        return self._chat_model
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate response using GPT."""
        
        lc_messages = self._convert_messages(messages)
        
        try:
            response = await self._chat_model.ainvoke(
                lc_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return LLMResponse(
                content=response.content,
                model=self.model,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if hasattr(response, 'usage_metadata') else 0,
                finish_reason="stop",
                metadata={"provider": "openai"}
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class OpenRouterAdapter(LLMAdapter):
    """Adapter for OpenRouter API (compatible with free Mistral models)."""
    
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.openrouter_api_key
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
        
        # OpenRouter uses OpenAI-compatible API
        self._chat_model = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=30,  # 30 second timeout to prevent hanging
            max_retries=2,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Agentic Loan Sales System"
            }
        )
    
    def get_chat_model(self) -> BaseChatModel:
        return self._chat_model
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenRouter."""
        
        lc_messages = self._convert_messages(messages)
        
        try:
            response = await self._chat_model.ainvoke(
                lc_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return LLMResponse(
                content=response.content,
                model=self.model,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if hasattr(response, 'usage_metadata') else 0,
                finish_reason="stop",
                metadata={"provider": "openrouter"}
            )
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise


class MockLLMAdapter(LLMAdapter):
    """Mock adapter for testing without API calls."""
    
    def __init__(self):
        self.model = "mock-model"
    
    def get_chat_model(self) -> BaseChatModel:
        return None
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Return mock response."""
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        return LLMResponse(
            content=f"Mock response to: {last_user_msg[:50]}...",
            model=self.model,
            tokens_used=100,
            finish_reason="stop",
            metadata={"provider": "mock"}
        )


def get_llm_adapter(provider: str = None) -> LLMAdapter:
    """
    Factory function to get LLM adapter.
    
    Args:
        provider: LLM provider ('anthropic', 'openai', 'openrouter', 'mock')
    
    Returns:
        Configured LLM adapter instance.
    """
    provider = provider or settings.llm_provider
    
    adapters = {
        "anthropic": AnthropicAdapter,
        "openai": OpenAIAdapter,
        "openrouter": OpenRouterAdapter,
        "mock": MockLLMAdapter,
    }
    
    adapter_class = adapters.get(provider.lower())
    
    if not adapter_class:
        logger.warning(f"Unknown LLM provider: {provider}, using mock")
        return MockLLMAdapter()
    
    return adapter_class()
