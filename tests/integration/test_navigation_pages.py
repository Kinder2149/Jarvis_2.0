"""
Tests d'intégration — Navigation API
Vérifie que les routes API principales sont accessibles.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client(temp_db_path):
    """TestClient avec DB temporaire."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            yield c


class TestRoutesAPI:
    """Routes API qui doivent être accessibles."""
    
    def test_route_projects_accessible(self, client):
        """GET /api/projects → 200."""
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    
    def test_route_chat_conversations_accessible(self, client):
        """GET /api/chat/conversations → 200."""
        resp = client.get("/api/chat/conversations")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    
    def test_route_atelier_prospects_accessible(self, client):
        """GET /api/atelier/prospects → 200."""
        resp = client.get("/api/atelier/prospects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    
    def test_route_config_accessible(self, client):
        """GET /api/config → 200."""
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "api_keys" in data
        assert "model_preferences" in data
    
    def test_route_pipelines_logs_accessible(self, client):
        """GET /api/pipelines/logs → 200 ou 422."""
        resp = client.get("/api/pipelines/logs?lines=10")
        # Accepter 200 ou 422 selon si project_id requis
        assert resp.status_code in [200, 422]
    
    def test_route_inexistante_retourne_404(self, client):
        """GET /api/route-inexistante → 404."""
        resp = client.get("/api/route-inexistante")
        assert resp.status_code == 404
    
    def test_route_projects_post_sans_data_retourne_422(self, client):
        """POST /api/projects sans données → 422."""
        resp = client.post("/api/projects", json={})
        assert resp.status_code == 422
    
    def test_route_chat_post_conversation_valide(self, client):
        """POST /api/chat/conversations avec titre → 200."""
        resp = client.post("/api/chat/conversations", json={"title": "Test"})
        assert resp.status_code == 200
        assert "id" in resp.json()
