"""
Tests pour RAGClient
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.services.rag_client import RAGClient


@pytest.mark.asyncio
async def test_search_success():
    """Test recherche réussie."""
    client = RAGClient()
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "results": [
            {"source": "pattern1.md", "content": "Pattern CRUD complet"},
            {"source": "pattern2.md", "content": "Pattern API REST"}
        ]
    }
    
    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_http_client
        
        result = await client.search("pattern CRUD Python")
        
        assert result != ""
        assert "pattern1.md" in result
        assert "Pattern CRUD complet" in result


@pytest.mark.asyncio
async def test_search_timeout():
    """Test timeout recherche."""
    client = RAGClient()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=Exception("Timeout")
        )
        
        result = await client.search("pattern CRUD Python")
        assert result == ""


@pytest.mark.asyncio
async def test_search_server_error():
    """Test erreur serveur."""
    client = RAGClient()
    
    mock_response = AsyncMock()
    mock_response.status_code = 500
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await client.search("pattern CRUD Python")
        assert result == ""


@pytest.mark.asyncio
async def test_health_check_success():
    """Test health check réussi."""
    client = RAGClient()
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_failure():
    """Test health check échec."""
    client = RAGClient()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection error")
        )
        
        result = await client.health_check()
        assert result is False
