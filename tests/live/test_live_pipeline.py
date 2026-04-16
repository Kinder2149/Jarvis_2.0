"""
Tests LIVE — Appels OpenRouter réels, simulent de vrais projets.

Marqués @pytest.mark.live — ne s'exécutent PAS dans la suite normale.
Commande : pytest tests/live/ -v --tb=short

Prérequis :
  - JARVIS doit tourner : uvicorn backend.main:app --reload --port 8000
  - config.json doit avoir une clé openrouter_key valide
"""
import pytest
import httpx
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

pytestmark = pytest.mark.live


# ─── Helpers ──────────────────────────────────────────────────────────────────

def api(method: str, path: str, **kwargs):
    """Appelle l'API JARVIS locale et lève une assertion si le statut est >= 400."""
    url = f"{BASE_URL}{path}"
    response = getattr(httpx, method)(url, timeout=120.0, **kwargs)
    assert response.status_code < 400, (
        f"{method.upper()} {path} → {response.status_code}\n{response.text[:500]}"
    )
    return response.json()


def wait_for_step(session_id: int, expected_statuses: list, max_wait: int = 120) -> dict:
    """Interroge la session jusqu'à ce que le statut souhaité soit atteint."""
    for _ in range(max_wait // 5):
        time.sleep(5)
        session = api("get", f"/pipelines/{session_id}")
        if session["status"] in expected_statuses:
            return session
    raise TimeoutError(
        f"Session {session_id} n'a pas atteint {expected_statuses} en {max_wait}s. "
        f"Statut actuel : {session.get('status')}"
    )


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def live_project(tmp_path_factory):
    """
    Crée un projet de test réel avec un PROJET_CONTEXTE.md simulant un vrai projet.
    Enregistre le projet dans JARVIS et le supprime après les tests.
    """
    project_dir = tmp_path_factory.mktemp("live_project")

    (project_dir / "PROJET_CONTEXTE.md").write_text(
        "## 1. IDENTITÉ\n"
        "| Nom | LiveTest App |\n"
        "| Type | web |\n"
        "| Objectif | Application de gestion de tâches |\n"
        "| Statut | En développement |\n\n"
        "## 2. STACK TECHNIQUE\n"
        "FastAPI + SQLite + HTML/JS vanilla\n\n"
        "## 3. ARCHITECTURE\n"
        "backend/ (FastAPI, routes, services)\n"
        "frontend/ (HTML, CSS, JS)\n"
        "data/ (SQLite)\n\n"
        "## 4. FONCTIONNALITÉS\n"
        "✅ Stables : création de tâches, liste des tâches\n"
        "❌ Bugs connus : la suppression de tâche renvoie 500\n\n"
        "## 8. SESSION EN COURS\n"
        "Objectif : corriger le bug de suppression\n\n"
        "## 9. BACKLOG\n"
        "1. Corriger bug suppression\n"
        "2. Ajouter filtres par statut\n",
        encoding="utf-8"
    )

    (project_dir / "backend").mkdir()
    (project_dir / "backend" / "routes.py").write_text(
        "from fastapi import APIRouter\nrouter = APIRouter()\n"
        "@router.delete('/tasks/{id}')\ndef delete_task(id: int):\n    raise Exception('Not implemented')\n"
    )

    project = api("post", "/projects", json={
        "name": "LiveTest App",
        "path": str(project_dir),
        "type": "web"
    })

    yield project

    # Nettoyage
    try:
        httpx.delete(f"{BASE_URL}/projects/{project['id']}", timeout=10)
    except Exception:
        pass


# ─── Tests live ───────────────────────────────────────────────────────────────

class TestLiveConnection:
    """Vérifie que le serveur JARVIS est démarré et répond."""

    def test_serveur_en_ligne(self):
        try:
            response = httpx.get(f"{BASE_URL}/config", timeout=5)
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Serveur JARVIS non démarré. Lancez : uvicorn backend.main:app --reload --port 8000")

    def test_config_a_une_cle_openrouter(self):
        data = api("get", "/config")
        key = data["api_keys"]["openrouter_key"]
        assert key, "Aucune clé OpenRouter configurée dans config.json"
        # La clé est masquée → doit commencer par "..."
        assert key.startswith("..."), f"Clé inattendue (non masquée ?) : {key}"

    def test_modeles_disponibles_non_vides(self):
        data = api("get", "/config/models/available")
        for cat in ["routing", "structuring", "code", "analysis"]:
            assert len(data[cat]) > 0


class TestLiveSessionStart:
    """Lance session_start avec un vrai appel Gemini Flash."""

    def test_session_start_complete(self, live_project):
        result = api("post", "/pipelines/start", json={
            "project_id": live_project["id"],
            "workflow_type": "session_start",
            "initial_input": ""
        })

        session = result["session"]
        exec_result = result["execution_result"]

        assert session["status"] == "COMPLETED", (
            f"session_start devrait être COMPLETED, got {session['status']}"
        )
        assert exec_result["status"] == "completed"

        step = session["steps"][0]
        assert step["status"] == "COMPLETED"
        assert step["output_data"] is not None
        assert len(step["output_data"]) > 10, "Output trop court, probable erreur silencieuse"
        assert step["model_used"] is not None

        print(f"\n[OK] session_start — modèle utilisé : {step['model_used']}")
        print(f"[OK] Output step 0 (extrait) : {step['output_data'][:200]}")


class TestLiveBugSimple:
    """Lance le workflow bug_simple en entier, avec validations humaines simulées."""

    def test_bug_simple_etape_par_etape(self, live_project):
        """
        Scénario complet :
        - Start → steps 0+1 auto (routing + collecte_info)
        - Step 2 (diagnostic) → WAITING_VALIDATION → Approuver
        - Step 3 (correction) → WAITING_VALIDATION → Approuver
        - Step 4 (cloture) → auto → COMPLETED
        """
        bug_description = (
            "La route DELETE /tasks/{id} renvoie une erreur 500 'Not implemented'. "
            "Le bug est dans backend/routes.py ligne 4. "
            "La suppression en base de données n'est pas implémentée."
        )

        # ── DÉMARRAGE ──────────────────────────────────────────────────────
        result = api("post", "/pipelines/start", json={
            "project_id": live_project["id"],
            "workflow_type": "bug_simple",
            "initial_input": bug_description
        })
        session = result["session"]
        session_id = session["id"]

        print(f"\n[INFO] Session créée : {session_id}")
        print(f"[INFO] Statut initial : {session['status']}")

        steps = {s["step_name"]: s for s in session["steps"]}

        # ── VÉRIFICATION STEPS 0+1 AUTO ────────────────────────────────────
        assert steps["routing"]["status"] == "COMPLETED", (
            f"Step 'routing' devrait être COMPLETED, got {steps['routing']['status']}"
        )
        assert steps["collecte_info"]["status"] == "COMPLETED", (
            f"Step 'collecte_info' devrait être COMPLETED, got {steps['collecte_info']['status']}"
        )

        routing_output = steps["routing"]["output_data"]
        assert routing_output, "routing n'a produit aucun output"
        print(f"[OK] routing output : {routing_output[:100]}")

        collecte_output = steps["collecte_info"]["output_data"]
        assert collecte_output, "collecte_info n'a produit aucun output"
        print(f"[OK] collecte_info output : {collecte_output[:100]}")

        # ── STEP 2 : DIAGNOSTIC (WAITING_VALIDATION) ────────────────────────
        assert session["status"] == "WAITING_VALIDATION", (
            f"Session devrait être WAITING_VALIDATION après step 2, got {session['status']}"
        )
        diag_step = steps["diagnostic"]
        assert diag_step["status"] == "WAITING_VALIDATION"
        assert diag_step["output_data"], "diagnostic n'a produit aucun output"
        print(f"[OK] diagnostic output : {diag_step['output_data'][:200]}")

        # Simuler approbation humaine du diagnostic
        val1 = api("post", f"/pipelines/{session_id}/validate/{diag_step['id']}", json={
            "approved": True,
            "edited_output": None
        })
        print(f"[OK] Validation diagnostic → {val1['validation_result']['status']}")

        # ── STEP 3 : CORRECTION (WAITING_VALIDATION) ────────────────────────
        session_after_val1 = val1["session"]
        steps_after_val1 = {s["step_name"]: s for s in session_after_val1["steps"]}

        assert session_after_val1["status"] == "WAITING_VALIDATION", (
            f"Session devrait être en WAITING_VALIDATION pour correction, "
            f"got {session_after_val1['status']}"
        )
        corr_step = steps_after_val1["correction"]
        assert corr_step["status"] == "WAITING_VALIDATION"
        assert corr_step["output_data"], "correction n'a produit aucun output"
        assert corr_step["output_type"] == "diff", "correction devrait être output_type=diff"
        print(f"[OK] correction output (extrait) : {corr_step['output_data'][:200]}")

        # Simuler approbation de la correction
        val2 = api("post", f"/pipelines/{session_id}/validate/{corr_step['id']}", json={
            "approved": True,
            "edited_output": None
        })
        print(f"[OK] Validation correction → {val2['validation_result']['status']}")

        # ── STEP 4 : CLÔTURE (AUTO) → COMPLETED ─────────────────────────────
        final_session = val2["session"]
        assert final_session["status"] == "COMPLETED", (
            f"Session devrait être COMPLETED en fin, got {final_session['status']}"
        )

        final_steps = {s["step_name"]: s for s in final_session["steps"]}
        cloture_step = final_steps["cloture"]
        assert cloture_step["status"] == "COMPLETED"
        assert cloture_step["output_data"], "cloture n'a produit aucun output"

        print(f"\n{'='*60}")
        print(f"[SUCCESS] Pipeline bug_simple complété !")
        print(f"  Session ID   : {session_id}")
        print(f"  Statut final : {final_session['status']}")
        print(f"  Steps        : " + ", ".join(
            f"{s['step_name']}({s['status']})" for s in final_session["steps"]
        ))
        print(f"{'='*60}")


class TestLiveModelDecisionLog:
    """Vérifie que les appels modèles sont bien logués."""

    def test_log_cree_apres_session_start(self, live_project):
        # Utiliser la DB directement via l'API n'est pas possible,
        # mais on peut vérifier indirectement que model_used est rempli
        result = api("post", "/pipelines/start", json={
            "project_id": live_project["id"],
            "workflow_type": "session_start",
            "initial_input": ""
        })
        step = result["session"]["steps"][0]
        assert step["model_used"] is not None, "model_used non rempli — log manquant ?"
        assert "google" in step["model_used"] or "anthropic" in step["model_used"], (
            f"model_used inattendu : {step['model_used']}"
        )
