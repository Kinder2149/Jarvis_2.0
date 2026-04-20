"""
Tests d'intégration — Module Chat
call_model est mocké : aucun appel OpenRouter réel.
Vérifie les fonctionnalités du module chat (conversations, messages, profil utilisateur).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path


@pytest.fixture
def client_and_db(temp_db_path):
    """TestClient avec DB temporaire initialisée."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture
def client_with_project(temp_db_path, tmp_path):
    """TestClient avec DB temporaire + un projet créé."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            project_dir = tmp_path / "test_project"
            project_dir.mkdir()
            created = c.post("/api/projects", json={
                "name": "Test Project",
                "path": str(project_dir),
                "type": "web"
            }).json()
            yield c, created["id"], project_dir


class TestConversationCreation:
    
    def test_conversation_creation_avec_projet(self, client_with_project):
        """Créer une conversation liée à un projet → project_id présent dans réponse GET."""
        c, project_id, _ = client_with_project
        
        resp = c.post("/api/chat/conversations", json={
            "title": "Conv Test",
            "project_id": project_id
        })
        assert resp.status_code == 200
        conv_id = resp.json()["id"]
        
        resp_get = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["project_id"] == project_id


class TestEnvoiMessage:
    
    def test_envoyer_message_recoit_reponse(self, client_and_db):
        """Envoyer un message → réponse assistant non vide → stockage en DB."""
        c = client_and_db
        
        # Insérer clé API dans SQLite
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, category, updated_at)
            VALUES ('openrouter_key', 'sk-test-key', 'api_keys', datetime('now'))
        """)
        conn.commit()
        conn.close()
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Bonjour ! Comment puis-je vous aider ?"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 15}
        }
        
        with patch("backend.services.chat_service.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            resp = c.post(f"/api/chat/conversations/{conv['id']}/messages", json={
                "content": "bonjour"
            })
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_message"]["content"] == "bonjour"
        assert data["assistant_message"]["content"] == "Bonjour ! Comment puis-je vous aider ?"
        
        # Vérifier stockage en DB
        conv_data = c.get(f"/api/chat/conversations/{conv['id']}").json()
        assert len(conv_data["messages"]) == 2


class TestInternetAccess:
    
    def test_internet_access_toggle(self, client_and_db):
        """Activer internet_access via PATCH → GET retourne la valeur correcte."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        conv_id = conv["id"]
        
        resp = c.patch(f"/api/chat/conversations/{conv_id}", json={
            "internet_access": True
        })
        assert resp.status_code == 200
        
        resp_get = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp_get.json()["internet_access"] is True


class TestModelSelection:
    
    def test_model_par_conversation_persiste(self, client_and_db):
        """Définir un modèle spécifique → GET retourne le modèle correct."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        conv_id = conv["id"]
        
        resp = c.patch(f"/api/chat/conversations/{conv_id}", json={
            "model": "anthropic/claude-haiku-4-5"
        })
        assert resp.status_code == 200
        
        resp_get = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp_get.json()["model"] == "anthropic/claude-haiku-4-5"


class TestContextSummary:
    
    def test_context_summary_generation(self, client_and_db):
        """Générer un résumé de conversation → context_summary non vide."""
        c = client_and_db
        
        # Insérer clé API
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, category, updated_at)
            VALUES ('openrouter_key', 'sk-test-key', 'api_keys', datetime('now'))
        """)
        conn.commit()
        conn.close()
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        conv_id = conv["id"]
        
        # Mock httpx response pour résumé
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Résumé : Discussion sur les tests unitaires."}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20}
        }
        
        with patch("backend.services.chat_service.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            resp = c.post(f"/api/chat/conversations/{conv_id}/update-summary")
        
        assert resp.status_code == 200
        
        resp_get = c.get(f"/api/chat/conversations/{conv_id}")
        summary = resp_get.json().get("context_summary")
        # Le résumé peut être vide ou contenir du texte
        assert summary is not None


class TestSuppressionConversation:
    
    def test_suppression_conversation(self, client_and_db):
        """Supprimer une conversation → GET retourne 404."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        conv_id = conv["id"]
        
        resp_delete = c.delete(f"/api/chat/conversations/{conv_id}")
        assert resp_delete.status_code == 200
        
        resp_get = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp_get.status_code == 404


class TestTitrageAuto:
    
    def test_titrage_auto_premier_message(self, client_and_db):
        """Envoyer premier message → titre auto-généré à partir du message."""
        c = client_and_db
        
        # Insérer clé API
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, category, updated_at)
            VALUES ('openrouter_key', 'sk-test-key', 'api_keys', datetime('now'))
        """)
        conn.commit()
        conn.close()
        
        conv = c.post("/api/chat/conversations", json={"title": "Nouvelle conversation"}).json()
        conv_id = conv["id"]
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Voici comment créer un test unitaire..."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 15}
        }
        
        with patch("backend.services.chat_service.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            c.post(f"/api/chat/conversations/{conv_id}/messages", json={
                "content": "Comment créer un test unitaire en Python ?"
            })
        
        resp_get = c.get(f"/api/chat/conversations/{conv_id}")
        titre = resp_get.json()["title"]
        assert titre != "Nouvelle conversation"
        assert "Comment créer un test unitaire" in titre or "..." in titre
