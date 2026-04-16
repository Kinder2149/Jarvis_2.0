"""
Tests d'intégration — routes /api/pipelines
call_model est mocké : aucun appel OpenRouter réel.
Vérifie les transitions d'état du pipeline via l'API.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from pathlib import Path


@pytest.fixture
def client_and_project(temp_db_path, tmp_path):
    """
    TestClient avec DB temporaire + un projet créé et prêt.
    Retourne (client, project_id, project_path).
    """
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            # Créer un dossier projet avec un PROJET_CONTEXTE.md minimal
            project_dir = tmp_path / "jarvis_test_project"
            project_dir.mkdir()
            (project_dir / "PROJET_CONTEXTE.md").write_text(
                "## 1. IDENTITE\n| Nom | JARVIS Test |\n| Type | web |\n"
                "## 2. STACK TECHNIQUE\nFastAPI + SQLite\n"
                "## 3. ARCHITECTURE\nbackend/ + frontend/\n"
                "## 4. FONCTIONNALITES\nStables : login\n"
                "## 8. SESSION EN COURS\nObjectif : test\n"
                "## 9. BACKLOG\n1. Rien\n",
                encoding="utf-8"
            )

            created = c.post("/api/projects", json={
                "name": "JARVIS Test", "path": str(project_dir), "type": "web"
            }).json()
            project_id = created["id"]

            yield c, project_id, str(project_dir)


MOCK_RESPONSES = {
    "routing": '{"classification": "bug_simple", "description": "login renvoie 500"}',
    "collecte_info": "Questions : 1. Quel est le message d'erreur exact ? 2. Quel fichier ?",
    "diagnostic": "Couche : Logique. Cause : mauvaise gestion exception. Fichier : backend/routes/auth.py",
    "correction": "```python\n# backend/routes/auth.py\ntry:\n    ...\nexcept Exception as e:\n    raise HTTPException(500, str(e))\n```",
    "cloture": "Session cloturee. Fichiers modifies : backend/routes/auth.py",
}


async def _mock_call(model_id, messages, api_keys, session_id, step_name, model_type, db):
    """Side-effect async pour call_model : retourne une réponse mock selon le nom du step."""
    return MOCK_RESPONSES.get(step_name, f"mock output for {step_name}")


class TestStartPipeline:

    def test_start_retourne_200(self, client_and_project):
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call

            response = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "bug_simple",
                "initial_input": "Le login renvoie une erreur 500"
            })

        assert response.status_code == 200

    def test_start_retourne_session_et_execution_result(self, client_and_project):
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call

            data = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "bug_simple",
                "initial_input": "Bug: 500 sur login"
            }).json()

        assert "session" in data
        assert "execution_result" in data

    def test_session_creee_avec_5_steps(self, client_and_project):
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call

            data = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "bug_simple",
                "initial_input": "Bug test"
            }).json()

        assert len(data["session"]["steps"]) == 5

    def test_session_start_a_un_seul_step_completed(self, client_and_project):
        """session_start n'a qu'un step, pas de validation → doit être COMPLETED."""
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.return_value = "Résumé orientation en 5 lignes."

            data = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "session_start",
                "initial_input": ""
            }).json()

        assert data["session"]["status"] == "COMPLETED"
        assert data["execution_result"]["status"] == "completed"

    def test_404_si_projet_inconnu(self, client_and_project):
        c, _, _ = client_and_project
        response = c.post("/api/pipelines/start", json={
            "project_id": 99999,
            "workflow_type": "bug_simple",
            "initial_input": "test"
        })
        assert response.status_code == 404

    def test_auto_advance_steps_sans_validation(self, client_and_project):
        """Steps 0 et 1 de bug_simple sont sans validation → avancement auto jusqu'à step 2."""
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call

            data = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "bug_simple",
                "initial_input": "Bug: login 500"
            }).json()

        session = data["session"]
        steps = {s["step_name"]: s for s in session["steps"]}

        # Steps 0 (routing) et 1 (collecte_info) auto-complétés
        assert steps["routing"]["status"] == "COMPLETED"
        assert steps["collecte_info"]["status"] == "COMPLETED"
        # Step 2 (diagnostic) en attente de validation
        assert steps["diagnostic"]["status"] == "WAITING_VALIDATION"
        assert session["status"] == "WAITING_VALIDATION"


class TestGetPipeline:

    def test_get_session_existante(self, client_and_project):
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = lambda model_id, messages, api_keys, session_id, step_name, model_type, db: \
                _async_return("mock output")

            session_data = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "session_start",
                "initial_input": ""
            }).json()["session"]

        response = c.get(f"/api/pipelines/{session_data['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == session_data["id"]

    def test_404_pour_session_inconnue(self, client_and_project):
        c, _, _ = client_and_project
        response = c.get("/api/pipelines/99999")
        assert response.status_code == 404


class TestValidatePipeline:

    def _start_bug_simple(self, c, project_id):
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            data = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "bug_simple",
                "initial_input": "Bug: login 500"
            }).json()
        return data["session"]

    def test_validation_approbation_avance(self, client_and_project):
        c, project_id, _ = client_and_project
        session = self._start_bug_simple(c, project_id)
        session_id = session["id"]

        # Trouver le step en WAITING_VALIDATION
        waiting_step = next(s for s in session["steps"] if s["status"] == "WAITING_VALIDATION")
        step_id = waiting_step["id"]

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call

            response = c.post(f"/api/pipelines/{session_id}/validate/{step_id}", json={
                "approved": True,
                "edited_output": None
            })

        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "validation_result" in data

    def test_validation_rejet_abandonne_session(self, client_and_project):
        c, project_id, _ = client_and_project
        session = self._start_bug_simple(c, project_id)
        session_id = session["id"]
        waiting_step = next(s for s in session["steps"] if s["status"] == "WAITING_VALIDATION")

        response = c.post(f"/api/pipelines/{session_id}/validate/{waiting_step['id']}", json={
            "approved": False,
            "edited_output": None
        })

        assert response.status_code == 200
        data = response.json()
        assert data["session"]["status"] == "ABORTED"


class TestAbortPipeline:

    def test_abort_passe_en_aborted(self, client_and_project):
        c, project_id, _ = client_and_project

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            session = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "bug_simple",
                "initial_input": "test"
            }).json()["session"]

        response = c.post(f"/api/pipelines/{session['id']}/abort")
        assert response.status_code == 200
        assert response.json()["status"] == "ABORTED"


class TestGetLogs:
    """GET /pipelines/logs : lecture du fichier jarvis.log."""

    def test_logs_logique_fichier_existe(self, tmp_path):
        """Logique get_logs : fichier existe → retourne lignes."""
        from backend.routers.pipelines import get_logs
        
        log_path = tmp_path / "jarvis.log"
        log_path.write_text(
            "2026-04-16 12:00:00 | INFO | JARVIS démarré\n"
            "2026-04-16 12:01:00 | INFO | Session créée\n"
            "2026-04-16 12:02:00 | ERROR | Erreur test\n",
            encoding="utf-8"
        )
        
        # Patcher LOG_PATH dans le module
        import backend.routers.pipelines as pipelines_module
        original_path = pipelines_module.LOG_PATH
        try:
            pipelines_module.LOG_PATH = log_path
            result = get_logs(lines=10)
            
            assert "lines" in result
            assert len(result["lines"]) == 3
            assert "JARVIS démarré" in result["lines"][0]
        finally:
            pipelines_module.LOG_PATH = original_path

    def test_logs_logique_fichier_absent(self, tmp_path):
        """Logique get_logs : fichier absent → retourne vide."""
        from backend.routers.pipelines import get_logs
        
        fake_log_path = tmp_path / "nonexistent.log"
        
        import backend.routers.pipelines as pipelines_module
        original_path = pipelines_module.LOG_PATH
        try:
            pipelines_module.LOG_PATH = fake_log_path
            result = get_logs(lines=100)
            
            assert result["lines"] == []
        finally:
            pipelines_module.LOG_PATH = original_path

    def test_logs_logique_limite_lignes(self, tmp_path):
        """Logique get_logs : limite nombre de lignes retournées."""
        from backend.routers.pipelines import get_logs
        
        log_path = tmp_path / "jarvis.log"
        lines_content = "\n".join([f"2026-04-16 12:{i:02d}:00 | INFO | Log {i}" for i in range(20)])
        log_path.write_text(lines_content, encoding="utf-8")
        
        import backend.routers.pipelines as pipelines_module
        original_path = pipelines_module.LOG_PATH
        try:
            pipelines_module.LOG_PATH = log_path
            result = get_logs(lines=5)
            
            assert len(result["lines"]) == 5
            assert "Log 15" in result["lines"][0]
            assert "Log 19" in result["lines"][4]
        finally:
            pipelines_module.LOG_PATH = original_path

    def test_logs_logique_default_100_lignes(self, tmp_path):
        """Logique get_logs : default 100 lignes max."""
        from backend.routers.pipelines import get_logs
        
        log_path = tmp_path / "jarvis.log"
        lines_content = "\n".join([f"Log {i}" for i in range(150)])
        log_path.write_text(lines_content, encoding="utf-8")
        
        import backend.routers.pipelines as pipelines_module
        original_path = pipelines_module.LOG_PATH
        try:
            pipelines_module.LOG_PATH = log_path
            result = get_logs(lines=100)
            
            assert len(result["lines"]) == 100
        finally:
            pipelines_module.LOG_PATH = original_path


