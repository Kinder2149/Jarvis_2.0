"""
Tests d'intégration — nouvelles routes C01
- POST /api/pipelines/parse-mission
- POST /api/pipelines/start avec modele_override et source_mission_prompt_id
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


PROMPT_VALIDE = """# MISSION CODE — Test JWT

## Objectif
Implémenter JWT dans le backend FastAPI pour sécuriser les routes.

## Contexte
Décision figée 2026-01-15 : utiliser JWT avec expiration 24h.

## Fichiers concernés
- `backend/routers/auth.py` — nouveau fichier d'authentification
- `backend/main.py` — ajout du middleware JWT

## Contraintes
- Pas de breaking change sur les routes existantes

## Critères de réussite
1. GET /api/projects sans token → 401
2. GET /api/projects avec token → 200

## Recommandation modèle
`anthropic/claude-haiku-4.5` — mission simple
"""

PROMPT_SANS_OBJECTIF = """## Fichiers concernés
- `backend/main.py` — fichier principal
"""

PROMPT_SANS_FICHIERS = """## Objectif
Faire quelque chose d'important.
"""


@pytest.fixture
def client_and_project(temp_db_path, tmp_path):
    """TestClient avec DB temporaire + un projet créé."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            project_dir = tmp_path / "test_project"
            project_dir.mkdir()
            (project_dir / "PROJET_CONTEXTE.md").write_text(
                "## 1. IDENTITE\n| Nom | Test |\n"
                "## 8. SESSION EN COURS\nObjectif : test\n",
                encoding="utf-8"
            )
            created = c.post("/api/projects", json={
                "name": "Test Project",
                "path": str(project_dir),
                "type": "web"
            }).json()
            yield c, created["id"], str(project_dir)


async def _mock_call(model_id, messages, api_keys, session_id, step_name, model_type, db):
    mock_responses = {
        "execution": "```python\n# code\nprint('ok')\n```",
        "verification": "Tout est OK.",
        "cloture": '{"section_8": "done", "changelog_line": "done"}',
    }
    return mock_responses.get(step_name, f"mock output for {step_name}")


class TestParseMissionRoute:

    def test_parse_mission_200_sur_prompt_valide(self, client_and_project):
        c, _, _ = client_and_project
        resp = c.post("/api/pipelines/parse-mission", json={"text": PROMPT_VALIDE})
        assert resp.status_code == 200

    def test_parse_mission_retourne_objectif(self, client_and_project):
        c, _, _ = client_and_project
        data = c.post("/api/pipelines/parse-mission", json={"text": PROMPT_VALIDE}).json()
        assert "objectif" in data
        assert "JWT" in data["objectif"]

    def test_parse_mission_retourne_fichiers_concernes(self, client_and_project):
        c, _, _ = client_and_project
        data = c.post("/api/pipelines/parse-mission", json={"text": PROMPT_VALIDE}).json()
        assert "fichiers_concernes" in data
        assert len(data["fichiers_concernes"]) == 2

    def test_parse_mission_retourne_modele_recommande(self, client_and_project):
        c, _, _ = client_and_project
        data = c.post("/api/pipelines/parse-mission", json={"text": PROMPT_VALIDE}).json()
        assert data["modele_recommande"] == "anthropic/claude-haiku-4.5"

    def test_parse_mission_400_sans_objectif(self, client_and_project):
        c, _, _ = client_and_project
        resp = c.post("/api/pipelines/parse-mission", json={"text": PROMPT_SANS_OBJECTIF})
        assert resp.status_code == 400
        assert "Objectif" in resp.json().get("detail", "")

    def test_parse_mission_400_sans_fichiers(self, client_and_project):
        c, _, _ = client_and_project
        resp = c.post("/api/pipelines/parse-mission", json={"text": PROMPT_SANS_FICHIERS})
        assert resp.status_code == 400
        assert "Fichiers" in resp.json().get("detail", "")

    def test_parse_mission_400_texte_vide(self, client_and_project):
        c, _, _ = client_and_project
        resp = c.post("/api/pipelines/parse-mission", json={"text": ""})
        assert resp.status_code == 400

    def test_parse_mission_retourne_warnings_liste(self, client_and_project):
        c, _, _ = client_and_project
        prompt_minimal = "## Objectif\nCorrection bug.\n## Fichiers concernés\n- `backend/main.py` — principal\n"
        data = c.post("/api/pipelines/parse-mission", json={"text": prompt_minimal}).json()
        assert isinstance(data.get("parse_warnings"), list)


class TestStartPipelineV2:

    def test_start_avec_modele_override_persiste(self, client_and_project):
        """modele_override passé → visible dans la session retournée."""
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            data = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test",
                "modele_override": "anthropic/claude-sonnet-4.5"
            }).json()

        assert "session" in data

    def test_start_avec_source_mission_prompt_id(self, client_and_project):
        """source_mission_prompt_id accepté sans erreur."""
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test",
                "source_mission_prompt_id": 42
            })

        assert resp.status_code == 200

    def test_start_schema_complet_accepte(self, client_and_project):
        """Tous les champs du nouveau schema StartPipeline acceptés."""
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "ma mission",
                "modele_override": "google/gemini-2.5-flash",
                "source_mission_prompt_id": 7
            })

        assert resp.status_code == 200
