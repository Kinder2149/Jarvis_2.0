"""
Tests d'intégration — routes /api/jarvis
Couvre : conversations CRUD, chat (avec mock process_message).
Aucun appel LLM réel.

NOTE: Ces tests ont une limitation connue avec APScheduler et les event loops fermés.
Le premier test passe, mais les suivants échouent avec "RuntimeError: Event loop is closed".
Cela est dû au scheduler APScheduler dans backend/main.py qui démarre au startup de l'app.
Les tests unitaires dans test_jarvis_agents.py et test_jarvis_routing.py couvrent la logique
métier sans ce problème d'infrastructure.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.fixture(scope="function")
def client(temp_db_path):
    """Fixture client pour chaque test."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        
        with TestClient(app) as c:
            yield c


class TestJarvisConversations:

    def test_creer_conversation(self, client):
        r = client.post("/api/jarvis/conversations", json={"title": "Test conv"})
        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert data["title"] == "Test conv"

    def test_lister_conversations_vide(self, client):
        r = client.get("/api/jarvis/conversations")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_lister_conversations_retourne_creees(self, client):
        client.post("/api/jarvis/conversations", json={"title": "Conv 1"})
        client.post("/api/jarvis/conversations", json={"title": "Conv 2"})
        r = client.get("/api/jarvis/conversations")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2

    def test_get_conversation_avec_messages(self, client):
        r = client.post("/api/jarvis/conversations", json={"title": "Détail test"})
        conv_id = r.json()["id"]
        r2 = client.get(f"/api/jarvis/conversations/{conv_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["id"] == conv_id
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_get_conversation_inexistante(self, client):
        r = client.get("/api/jarvis/conversations/99999")
        assert r.status_code == 404

    def test_supprimer_conversation(self, client):
        r = client.post("/api/jarvis/conversations", json={"title": "À supprimer"})
        conv_id = r.json()["id"]
        r2 = client.delete(f"/api/jarvis/conversations/{conv_id}")
        assert r2.status_code in (200, 204)
        r3 = client.get(f"/api/jarvis/conversations/{conv_id}")
        assert r3.status_code == 404


class TestJarvisChat:

    def test_chat_retourne_message_assistant(self, client):
        r = client.post("/api/jarvis/conversations", json={"title": "Chat test"})
        conv_id = r.json()["id"]

        mock_response = {
            "role": "assistant",
            "content": "Bonjour, je suis JARVIS.",
            "agent": "JARVIS",
            "instance_ref": None
        }

        with patch(
            "backend.services.jarvis_service.process_message",
            new=AsyncMock(return_value={
                "message": mock_response,
                "suggest_freeze": False,
                "freeze_reason": None
            })
        ):
            r2 = client.post(f"/api/jarvis/conversations/{conv_id}/chat", json={"message": "Bonjour"})

        assert r2.status_code == 200
        data = r2.json()
        assert "message" in data
        assert data["message"]["role"] == "assistant"
        assert data["message"]["agent"] == "JARVIS"
        assert data["suggest_freeze"] is False

    def test_chat_conversation_inexistante(self, client):
        with patch(
            "backend.services.jarvis_service.process_message",
            new=AsyncMock(return_value={
                "message": {"role": "assistant", "content": "ok", "agent": "JARVIS", "instance_ref": None},
                "suggest_freeze": False,
                "freeze_reason": None
            })
        ):
            r = client.post("/api/jarvis/conversations/99999/chat", json={"message": "test"})
        assert r.status_code == 404

    def test_messages_sauvegardes_apres_chat(self, client):
        r = client.post("/api/jarvis/conversations", json={"title": "Persistance"})
        conv_id = r.json()["id"]

        with patch(
            "backend.services.jarvis_service.process_message",
            new=AsyncMock(return_value={
                "message": {"role": "assistant", "content": "Réponse test", "agent": "MENTOR", "instance_ref": None},
                "suggest_freeze": False,
                "freeze_reason": None
            })
        ):
            client.post(f"/api/jarvis/conversations/{conv_id}/chat", json={"message": "Message test"})

        r2 = client.get(f"/api/jarvis/conversations/{conv_id}")
        messages = r2.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Message test"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["agent"] == "MENTOR"
