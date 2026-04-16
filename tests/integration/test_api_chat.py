"""
Tests d'intégration — API Chat (/api/chat/*)
Vérifie les routes conversations et messages avec mock httpx.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def client_and_db(temp_db_path):
    """Client FastAPI avec DB temporaire."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            yield c


class TestCreateConversation:
    """POST /api/chat/conversations"""

    def test_creation_sans_projet(self, client_and_db):
        """Création conversation sans projet → 200, retourne id + title."""
        c = client_and_db
        
        response = c.post("/api/chat/conversations", json={"title": "Test Chat"})
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Chat"
        assert data["project_id"] is None

    def test_creation_avec_projet(self, client_and_db):
        """Création avec project_id → project_id présent dans réponse."""
        c = client_and_db
        
        # Créer un projet d'abord
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test Project",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            response = c.post("/api/chat/conversations", json={
                "project_id": project["id"],
                "title": "Chat Projet"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == project["id"]


class TestListConversations:
    """GET /api/chat/conversations"""

    def test_liste_vide_au_debut(self, client_and_db):
        """Aucune conversation → liste vide."""
        c = client_and_db
        
        response = c.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_liste_avec_conversations(self, client_and_db):
        """Conversations créées → retournées dans la liste."""
        c = client_and_db
        
        c.post("/api/chat/conversations", json={"title": "Conv 1"})
        c.post("/api/chat/conversations", json={"title": "Conv 2"})
        
        response = c.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("message_count" in conv for conv in data)

    def test_filtre_par_projet(self, client_and_db):
        """Filtre project_id → retourne seulement conversations du projet."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            # Créer 1 conv avec projet, 1 sans
            c.post("/api/chat/conversations", json={"project_id": project["id"], "title": "Avec projet"})
            c.post("/api/chat/conversations", json={"title": "Sans projet"})
            
            response = c.get(f"/api/chat/conversations?project_id={project['id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Avec projet"


class TestGetConversation:
    """GET /api/chat/conversations/{id}"""

    def test_get_conversation_existante(self, client_and_db):
        """Conversation existante → retourne messages (vide au début)."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        
        response = c.get(f"/api/chat/conversations/{conv['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv["id"]
        assert data["title"] == "Test"
        assert "messages" in data
        assert len(data["messages"]) == 0

    def test_get_conversation_inexistante(self, client_and_db):
        """Conversation inexistante → 404."""
        c = client_and_db
        
        response = c.get("/api/chat/conversations/99999")
        
        assert response.status_code == 404


class TestSendMessage:
    """POST /api/chat/conversations/{id}/messages"""

    def test_envoi_message_mock_httpx(self, client_and_db):
        """Envoi message avec mock httpx → 200, 2 messages créés."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Réponse assistant"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            response = c.post(f"/api/chat/conversations/{conv['id']}/messages", json={
                "content": "Bonjour"
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_message" in data
        assert data["user_message"]["content"] == "Bonjour"
        assert data["user_message"]["role"] == "user"
        
        assert "assistant_message" in data
        assert data["assistant_message"]["content"] == "Réponse assistant"
        assert data["assistant_message"]["role"] == "assistant"
        
        # Vérifier que les messages sont bien en DB
        conv_data = c.get(f"/api/chat/conversations/{conv['id']}").json()
        assert len(conv_data["messages"]) == 2


class TestDeleteConversation:
    """DELETE /api/chat/conversations/{id}"""

    def test_suppression_conversation(self, client_and_db):
        """Suppression conversation → 200, {"deleted": true}."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "À supprimer"}).json()
        
        response = c.delete(f"/api/chat/conversations/{conv['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

    def test_get_apres_suppression(self, client_and_db):
        """GET après DELETE → 404."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        c.delete(f"/api/chat/conversations/{conv['id']}")
        
        response = c.get(f"/api/chat/conversations/{conv['id']}")
        
        assert response.status_code == 404

    def test_suppression_inexistante(self, client_and_db):
        """DELETE conversation inexistante → 404."""
        c = client_and_db
        
        response = c.delete("/api/chat/conversations/99999")
        
        assert response.status_code == 404
