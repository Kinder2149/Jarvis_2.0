"""
Configuration pytest pour les tests E2E JARVIS.
Fixtures partagées : base_url, API client, création/suppression conversations.
"""
import pytest
import httpx
from typing import Generator


BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url() -> str:
    """URL de base du serveur JARVIS."""
    return BASE_URL


@pytest.fixture
def api_client(base_url: str) -> Generator[httpx.Client, None, None]:
    """Client HTTP synchrone pour les tests API."""
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
async def async_api_client(base_url: str) -> Generator[httpx.AsyncClient, None, None]:
    """Client HTTP asynchrone pour les tests API."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def create_jarvis_conversation(api_client: httpx.Client):
    """
    Fixture pour créer une conversation JARVIS et la nettoyer après le test.
    Usage: conv_id = create_jarvis_conversation("Titre test")
    """
    created_ids = []
    
    def _create(title: str = "Test E2E") -> int:
        response = api_client.post("/api/jarvis/conversations", json={"title": title})
        assert response.status_code == 201, f"Échec création conversation: {response.text}"
        conv_id = response.json()["id"]
        created_ids.append(conv_id)
        return conv_id
    
    yield _create
    
    # Cleanup : supprimer toutes les conversations créées
    for conv_id in created_ids:
        try:
            api_client.delete(f"/api/jarvis/conversations/{conv_id}")
        except Exception:
            pass  # Ignorer les erreurs de cleanup


@pytest.fixture
def cleanup_test_config(api_client: httpx.Client):
    """
    Fixture pour nettoyer les clés API de test après les tests config.
    """
    yield
    
    # Restaurer une config vide après le test
    try:
        api_client.post("/api/config", json={
            "api_keys": {},
            "model_preferences": {
                "routing": "google/gemini-2.5-flash",
                "structuring": "google/gemini-2.5-flash",
                "code": "anthropic/claude-haiku-4.5",
                "analysis": "anthropic/claude-sonnet-4.5"
            },
            "chat": None
        })
    except Exception:
        pass
