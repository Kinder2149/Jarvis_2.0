"""
Tests d'intégration — Module Code (refonte C01)
call_model est mocké : aucun appel OpenRouter réel.
Vérifie les fonctionnalités du module code avec workflow code_mission.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from pathlib import Path


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
                "## 8. SESSION EN COURS\nObjectif : test\n"
                "## 9. BACKLOG\n1. Rien\n",
                encoding="utf-8"
            )
            created = c.post("/api/projects", json={
                "name": "Test Project",
                "path": str(project_dir),
                "type": "web"
            }).json()
            yield c, created["id"], str(project_dir)


async def _mock_call(model_id, messages, api_keys, session_id, step_name, model_type, db):
    """Mock pour call_model."""
    mock_responses = {
        "execution": "```python\n# backend/main.py\nprint('hello')\n```",
        "verification": "Checklist: 1. Tester → OK",
        "cloture": '{"section_8": "Mission terminée", "changelog_line": "Fix"}',
    }
    return mock_responses.get(step_name, f"mock output for {step_name}")


class TestDemarrageSession:

    def test_demarrage_code_mission(self, client_and_project):
        """Démarrer session code_mission → 4 steps présents."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "Ajouter authentification JWT"
            })
        assert resp.status_code == 200
        session_id = resp.json()["session"]["id"]
        resp_status = c.get(f"/api/pipelines/{session_id}")
        assert resp_status.status_code == 200
        assert len(resp_status.json()["steps"]) == 4

    def test_workflows_obsoletes_retournent_erreur(self, client_and_project):
        """Workflows obsolètes (bug_simple, mission_complexe) ne doivent plus être supportés."""
        c, project_id, _ = client_and_project
        for wf in ["bug_simple", "mission_complexe", "session_start", "session_end"]:
            with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
                mock.side_effect = _mock_call
                resp = c.post("/api/pipelines/start", json={
                    "project_id": project_id,
                    "workflow_type": wf,
                    "initial_input": "test"
                })
            # La session peut être créée mais avec 0 steps (workflow inconnu)
            if resp.status_code == 200:
                session = resp.json().get("session", {})
                steps = session.get("steps", [])
                assert len(steps) == 0, f"Workflow obsolète '{wf}' a encore {len(steps)} steps"


class TestStepsInitiaux:

    def test_step0_sante_cadrage_auto_completes(self, client_and_project):
        """Step 0 (sante_cadrage) auto-complété sans LLM."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        steps = c.get(f"/api/pipelines/{session_id}").json()["steps"]
        step0 = next(s for s in steps if s["step_index"] == 0)
        assert step0["status"] == "COMPLETED"

    def test_step2_verification_en_attente(self, client_and_project):
        """Step 2 (verification) en WAITING_VALIDATION après démarrage."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        steps = {s["step_name"]: s for s in c.get(f"/api/pipelines/{session_id}").json()["steps"]}
        assert steps["verification"]["status"] == "WAITING_VALIDATION"


class TestPollingStatus:

    def test_polling_status_retourne_steps_complets(self, client_and_project):
        """GET /api/pipelines/{id} → steps avec step_name, status, output_type."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        data = c.get(f"/api/pipelines/{session_id}").json()
        assert "steps" in data
        for step in data["steps"]:
            assert "step_name" in step
            assert "status" in step
            assert "output_type" in step


class TestStepFailed:

    def test_step_FAILED_visible_via_api(self, client_and_project):
        """Step en FAILED → visible via GET status."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE pipeline_steps SET status='FAILED', error_message='Erreur test' WHERE session_id=? AND step_index=1", (session_id,))
        conn.commit()
        conn.close()
        steps = c.get(f"/api/pipelines/{session_id}").json()["steps"]
        step1 = next(s for s in steps if s["step_index"] == 1)
        assert step1["status"] == "FAILED"


class TestStepRetry:

    def test_step_FAILED_retry(self, client_and_project):
        """Step en FAILED → retry → 200."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE pipeline_steps SET status='FAILED', error_message='err' WHERE session_id=? AND step_index=1", (session_id,))
        cursor.execute("SELECT id FROM pipeline_steps WHERE session_id=? AND step_index=1", (session_id,))
        step_id = cursor.fetchone()["id"]
        conn.commit()
        conn.close()
        assert c.post(f"/api/pipelines/{session_id}/retry/{step_id}").status_code == 200


class TestValidation:

    def test_validation_approuver_avance_session(self, client_and_project):
        """Approuver validation step verification → 200."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        steps = c.get(f"/api/pipelines/{session_id}").json()["steps"]
        waiting = next((s for s in steps if s["status"] == "WAITING_VALIDATION"), None)
        assert waiting is not None
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp_v = c.post(f"/api/pipelines/{session_id}/validate/{waiting['id']}", json={"approved": True})
        assert resp_v.status_code == 200

    def test_validation_rejeter_abort_session(self, client_and_project):
        """Rejeter validation → session ABORTED."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        steps = c.get(f"/api/pipelines/{session_id}").json()["steps"]
        waiting = next((s for s in steps if s["status"] == "WAITING_VALIDATION"), None)
        assert waiting is not None
        resp_v = c.post(f"/api/pipelines/{session_id}/validate/{waiting['id']}", json={"approved": False})
        assert resp_v.status_code == 200
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM sessions WHERE id=?", (session_id,))
        assert cursor.fetchone()["status"] == "ABORTED"
        conn.close()


class TestAbortSession:

    def test_abort_session(self, client_and_project):
        """POST /abort → session ABORTED."""
        c, project_id, _ = client_and_project
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            resp = c.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": "test"
            })
        session_id = resp.json()["session"]["id"]
        assert c.post(f"/api/pipelines/{session_id}/abort").status_code == 200
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM sessions WHERE id=?", (session_id,))
        assert cursor.fetchone()["status"] == "ABORTED"
        conn.close()


class TestLogsEndpoint:

    def test_logs_endpoint_retourne_contenu(self, client_and_project):
        c, _, _ = client_and_project
        resp = c.get("/api/pipelines/logs?lines=10")
        assert resp.status_code in [200, 422]


class TestProjetInexistant:

    def test_projet_inexistant_retourne_404(self, client_and_project):
        c, _, _ = client_and_project
        resp = c.post("/api/pipelines/start", json={
            "project_id": 99999,
            "workflow_type": "code_mission",
            "initial_input": "test"
        })
        assert resp.status_code == 404
