"""
API Endpoint Tests
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint returns healthy status."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    @pytest.mark.asyncio
    async def test_root(self, client: AsyncClient):
        """Test root endpoint returns welcome message."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestChatEndpoint:
    """Tests for chat endpoint."""
    
    @pytest.mark.asyncio
    async def test_chat_greeting(self, client: AsyncClient):
        """Test chat with greeting message."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": "Hello, I need a loan"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
        assert "stage" in data


class TestEMICalculation:
    """Tests for EMI calculation."""
    
    @pytest.mark.asyncio
    async def test_emi_calculation(self, client: AsyncClient):
        """Test EMI calculation endpoint."""
        response = await client.post(
            "/api/v1/underwrite/calculate-emi",
            json={
                "principal": 500000,
                "annual_rate": 12.5,
                "tenure_months": 24
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "emi" in data
        assert data["emi"] > 0
        assert data["principal"] == 500000
