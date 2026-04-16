"""
Tests d'intégration — routes /api/config
Utilise un fichier config temporaire pour ne pas toucher la config réelle.
"""
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from pathlib import Path


@pytest.fixture
def config_file(tmp_path):
    """Crée un config.json temporaire avec des données de test."""
    config = {
        "api_keys": {
            "openrouter_key": "sk-or-test-key-abcd",
            "anthropic_key": "",
            "google_key": ""
        },
        "model_preferences": {
            "routing": "google/gemini-2.0-flash-001",
            "structuring": "anthropic/claude-haiku-4.5",
            "code": "anthropic/claude-sonnet-4.5",
            "analysis": "anthropic/claude-opus-4.5"
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config, indent=2))
    return path


@pytest.fixture
def client(config_file):
    """TestClient avec config temporaire patchée."""
    with patch("backend.routers.models.CONFIG_PATH", config_file):
        from backend.main import app
        with TestClient(app) as c:
            yield c, config_file


class TestGetConfig:

    def test_retourne_200(self, client):
        c, _ = client
        response = c.get("/api/config")
        assert response.status_code == 200

    def test_contient_api_keys_et_model_preferences(self, client):
        c, _ = client
        data = c.get("/api/config").json()
        assert "api_keys" in data
        assert "model_preferences" in data

    def test_cle_openrouter_est_masquee(self, client):
        c, _ = client
        data = c.get("/api/config").json()
        key = data["api_keys"]["openrouter_key"]
        # Doit commencer par "..." et se terminer par les 4 derniers chars
        assert key.startswith("...")
        assert key.endswith("abcd")

    def test_model_preferences_sont_corrects(self, client):
        c, _ = client
        prefs = c.get("/api/config").json()["model_preferences"]
        assert prefs["routing"] == "google/gemini-2.0-flash-001"
        assert prefs["structuring"] == "anthropic/claude-haiku-4.5"
        assert prefs["code"] == "anthropic/claude-sonnet-4.5"
        assert prefs["analysis"] == "anthropic/claude-opus-4.5"


class TestSaveConfig:

    def test_sauvegarde_retourne_200(self, client):
        c, _ = client
        new_config = {
            "api_keys": {"openrouter_key": "sk-or-new", "anthropic_key": "", "google_key": ""},
            "model_preferences": {
                "routing": "google/gemini-2.5-flash",
                "structuring": "anthropic/claude-haiku-4.5",
                "code": "anthropic/claude-sonnet-4.5",
                "analysis": "anthropic/claude-opus-4.5"
            }
        }
        response = c.post("/api/config", json=new_config)
        assert response.status_code == 200

    def test_sauvegarde_ecrit_le_fichier(self, client):
        c, config_file = client
        new_config = {
            "api_keys": {"openrouter_key": "sk-or-nouvelle-cle", "anthropic_key": "", "google_key": ""},
            "model_preferences": {
                "routing": "google/gemini-2.5-flash",
                "structuring": "anthropic/claude-haiku-4.5",
                "code": "anthropic/claude-sonnet-4.5",
                "analysis": "anthropic/claude-opus-4.5"
            }
        }
        c.post("/api/config", json=new_config)
        saved = json.loads(config_file.read_text())
        assert saved["api_keys"]["openrouter_key"] == "sk-or-nouvelle-cle"
        assert saved["model_preferences"]["routing"] == "google/gemini-2.5-flash"


class TestAvailableModels:

    def test_retourne_200(self):
        from backend.main import app
        with TestClient(app) as c:
            response = c.get("/api/config/models/available")
        assert response.status_code == 200

    def test_contient_4_categories(self):
        from backend.main import app
        with TestClient(app) as c:
            data = c.get("/api/config/models/available").json()
        for cat in ["routing", "structuring", "code", "analysis"]:
            assert cat in data

    def test_routing_contient_gemini_flash(self):
        from backend.main import app
        with TestClient(app) as c:
            data = c.get("/api/config/models/available").json()
        assert "google/gemini-2.0-flash-001" in data["routing"]

    def test_code_contient_claude_sonnet_4_5(self):
        from backend.main import app
        with TestClient(app) as c:
            data = c.get("/api/config/models/available").json()
        assert "anthropic/claude-sonnet-4.5" in data["code"]

    def test_aucun_modele_deprecie(self):
        """Aucun slug déprécié dans la liste disponible."""
        deprecated = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "google/gemini-flash-2.0",
            "anthropic/claude-haiku-4-5",   # tiret au lieu de point
            "anthropic/claude-sonnet-4-5",
        ]
        from backend.main import app
        with TestClient(app) as c:
            data = c.get("/api/config/models/available").json()

        all_models = [m for cat in data.values() for m in cat]
        for dep in deprecated:
            assert dep not in all_models, f"Modèle déprécié '{dep}' présent dans /models/available"
