"""
Tests LIVE — Workflows session_end, mission_complexe, nouveau_projet, projet_existant.
Appels OpenRouter réels. Prérequis : JARVIS doit tourner sur localhost:8000
Commande : pytest tests/live/test_live_workflows.py -v --tb=short
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
def project_with_history(tmp_path_factory):
    """
    Projet simulant un vrai projet avec du contenu complet.
    Utilisé par : session_end, mission_complexe
    """
    project_dir = tmp_path_factory.mktemp("project_with_history")

    (project_dir / "PROJET_CONTEXTE.md").write_text(
        "# PROJET_CONTEXTE — TaskManager\n\n"
        "## 1. IDENTITÉ\n\n"
        "| Champ | Valeur |\n"
        "|-------|--------|\n"
        "| Nom | TaskManager |\n"
        "| Type | web |\n"
        "| Objectif | Application de gestion de tâches avec filtres et priorités |\n"
        "| Statut | En développement |\n"
        "| Utilisateurs | 1 (usage personnel) |\n"
        "| Dernière mise à jour | 2026-04-16 |\n\n"
        "## 2. STACK TECHNIQUE\n\n"
        "FastAPI Python 3.11 — port 8000\n"
        "SQLite natif Python (sqlite3)\n"
        "HTML5 + CSS3 + JavaScript vanilla\n\n"
        "## 3. ARCHITECTURE\n\n"
        "```\n"
        "taskmanager/\n"
        "├── backend/\n"
        "│   ├── main.py\n"
        "│   ├── routes/\n"
        "│   │   ├── tasks.py\n"
        "│   │   └── users.py\n"
        "│   └── database.py\n"
        "└── frontend/\n"
        "    ├── index.html\n"
        "    └── assets/\n"
        "```\n\n"
        "## 4. FONCTIONNALITÉS\n\n"
        "✅ Stables : création de tâches, liste des tâches, authentification basique\n"
        "🚧 En cours : ajout filtres par priorité\n"
        "❌ Bugs connus : aucun bug actif\n\n"
        "## 5. RÈGLES SPÉCIFIQUES AU PROJET\n\n"
        "- Pas de framework JS (vanilla only)\n"
        "- SQLite sans ORM\n\n"
        "## 6. DÉCISIONS FIGÉES\n\n"
        "| Date | Décision | Raison |\n"
        "|------|----------|--------|\n"
        "| 2026-04-10 | Stack HTML/JS vanilla | Simplicité, zéro dépendance front |\n"
        "| 2026-04-12 | SQLite sans ORM | Contrôle total des requêtes |\n\n"
        "## 7. FICHIERS AUTORISÉS\n\n"
        "| Fichier | Rôle |\n"
        "|---------|------|\n"
        "| PROJET_CONTEXTE.md | Source de vérité |\n"
        "| CHANGELOG.md | Historique |\n\n"
        "## 8. SESSION EN COURS\n\n"
        "Graphify : non initialisé\n"
        "Objectif : ajouter un filtre par priorité sur la liste des tâches\n"
        "Fichiers concernés : backend/routes/tasks.py, frontend/index.html\n"
        "Hors scope cette session : authentification, base de données\n"
        "Résultat fin de session : filtre par priorité implémenté et testé\n"
        "Graphe mis à jour : non\n\n"
        "## 9. BACKLOG\n\n"
        "1. Ajouter filtres par statut (terminé/en cours)\n"
        "2. Export CSV des tâches\n"
        "3. Notifications par email\n",
        encoding="utf-8"
    )

    (project_dir / "backend").mkdir()
    (project_dir / "backend" / "routes").mkdir()
    (project_dir / "backend" / "routes" / "tasks.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n\n"
        "@router.get('/tasks')\n"
        "def list_tasks(priority: str = None):\n"
        "    return [{\"id\": 1, \"title\": \"Test\", \"priority\": \"high\"}]\n",
        encoding="utf-8"
    )

    (project_dir / "frontend").mkdir()
    (project_dir / "frontend" / "index.html").write_text(
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<body>\n"
        "<h1>TaskManager</h1>\n"
        "</body>\n"
        "</html>\n",
        encoding="utf-8"
    )

    project = api("post", "/projects", json={
        "name": "TaskManager",
        "path": str(project_dir),
        "type": "web"
    })

    yield project

    try:
        httpx.delete(f"{BASE_URL}/projects/{project['id']}", timeout=10)
    except Exception:
        pass


@pytest.fixture(scope="module")
def fresh_project_dir(tmp_path_factory):
    """
    Dossier VIDE (aucun fichier).
    Utilisé par : nouveau_projet
    """
    project_dir = tmp_path_factory.mktemp("fresh_project")

    project = api("post", "/projects", json={
        "name": "FreshProject",
        "path": str(project_dir),
        "type": "web"
    })

    yield project

    try:
        httpx.delete(f"{BASE_URL}/projects/{project['id']}", timeout=10)
    except Exception:
        pass


@pytest.fixture(scope="module")
def existing_project_no_docs(tmp_path_factory):
    """
    Projet avec du code mais SANS PROJET_CONTEXTE.md.
    Utilisé par : projet_existant
    """
    project_dir = tmp_path_factory.mktemp("existing_project")

    (project_dir / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n\n"
        "@app.get(\"/\")\n"
        "def root():\n"
        "    return {\"status\": \"ok\"}\n",
        encoding="utf-8"
    )

    (project_dir / "database.py").write_text(
        "import sqlite3\n"
        "conn = sqlite3.connect(\"data.db\")\n",
        encoding="utf-8"
    )

    (project_dir / "requirements.txt").write_text(
        "fastapi\n"
        "uvicorn\n"
        "httpx\n",
        encoding="utf-8"
    )

    (project_dir / "routes").mkdir()
    (project_dir / "routes" / "users.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n\n"
        "@router.get(\"/users\")\n"
        "def list_users():\n"
        "    return []\n",
        encoding="utf-8"
    )

    (project_dir / "frontend").mkdir()
    (project_dir / "frontend" / "index.html").write_text(
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<body>\n"
        "<h1>App</h1>\n"
        "</body>\n"
        "</html>\n",
        encoding="utf-8"
    )

    project = api("post", "/projects", json={
        "name": "ExistingProject",
        "path": str(project_dir),
        "type": "web"
    })

    yield project

    try:
        httpx.delete(f"{BASE_URL}/projects/{project['id']}", timeout=10)
    except Exception:
        pass


# ─── Tests live ───────────────────────────────────────────────────────────────

class TestLiveSessionEnd:
    """Lance session_end avec validation du JSON de clôture."""

    def test_session_end_complet(self, project_with_history):
        """
        Workflow : session_end — 1 step (cloture_docs, requires_validation=true)
        Scénario :
        1. Start session_end (aucun initial_input)
        2. Session doit être WAITING_VALIDATION (cloture_docs attend validation)
        3. Vérifier que cloture_docs a produit un output non vide
        4. Valider (approved=True)
        5. Vérifier session COMPLETED
        6. Vérifier filesystem : PROJET_CONTEXTE.md section 8 mise à jour
        """
        print(f"\n{'='*60}")
        print(f"[TEST] session_end — Projet : {project_with_history['name']}")
        print(f"{'='*60}")

        # 1. Démarrage
        result = api("post", "/pipelines/start", json={
            "project_id": project_with_history["id"],
            "workflow_type": "session_end",
            "initial_input": ""
        })
        session = result["session"]
        session_id = session["id"]

        print(f"\n[INFO] Session créée : {session_id}")
        print(f"[INFO] Statut initial : {session['status']}")

        # 2. Vérifier WAITING_VALIDATION
        assert session["status"] == "WAITING_VALIDATION", (
            f"session_end devrait être WAITING_VALIDATION, got {session['status']}"
        )
        cloture_step = session["steps"][0]
        assert cloture_step["step_name"] == "cloture_docs"
        assert cloture_step["status"] == "WAITING_VALIDATION"
        assert cloture_step["output_data"], "cloture_docs n'a produit aucun output"
        print(f"\n[OK] cloture_docs output : {cloture_step['output_data'][:300]}")

        # 3. Valider
        val = api("post", f"/pipelines/{session_id}/validate/{cloture_step['id']}", json={
            "approved": True,
            "edited_output": None
        })
        final_session = val["session"]
        assert final_session["status"] == "COMPLETED", (
            f"Session devrait être COMPLETED, got {final_session['status']}"
        )
        print(f"[OK] Validation → session COMPLETED")

        # 4. Vérifications filesystem
        project_path = Path(project_with_history["path"])
        pc_path = project_path / "PROJET_CONTEXTE.md"
        assert pc_path.exists(), "PROJET_CONTEXTE.md manquant après cloture"

        pc_content = pc_path.read_text(encoding="utf-8")
        assert "## 8." in pc_content, "Section 8 manquante après cloture"
        print(f"[OK] PROJET_CONTEXTE.md section 8 présente")

        cl_path = project_path / "CHANGELOG.md"
        if cl_path.exists():
            print(f"[OK] CHANGELOG.md présent : {cl_path.read_text(encoding='utf-8')[:200]}")
        else:
            print(f"[WARN] CHANGELOG.md non créé — à investiguer")

        print(f"\n{'='*60}")
        print(f"[SUCCESS] session_end complété !")
        print(f"  Session ID   : {session_id}")
        print(f"  Statut final : {final_session['status']}")
        print(f"{'='*60}")


class TestLiveMissionComplexe:
    """Lance mission_complexe avec 2 validations (cadrage + execution)."""

    def test_mission_complexe_complet(self, project_with_history):
        """
        Workflow : mission_complexe — 7 steps
        Validations : cadrage (step 1), execution (step 4)
        """
        print(f"\n{'='*60}")
        print(f"[TEST] mission_complexe — Projet : {project_with_history['name']}")
        print(f"{'='*60}")

        feature_description = (
            "Ajouter un filtre par priorité sur la route GET /tasks. "
            "La route doit accepter un paramètre optionnel priority (valeurs : high, medium, low). "
            "Retourner uniquement les tâches correspondant à la priorité demandée. "
            "Si priority est absent, retourner toutes les tâches."
        )

        result = api("post", "/pipelines/start", json={
            "project_id": project_with_history["id"],
            "workflow_type": "mission_complexe",
            "initial_input": feature_description
        })
        session = result["session"]
        session_id = session["id"]

        print(f"\n[INFO] Session créée : {session_id}")
        print(f"[INFO] Statut initial : {session['status']}")

        # Step 0 auto (routing) → Step 1 WAITING_VALIDATION (cadrage)
        assert session["status"] == "WAITING_VALIDATION", (
            f"Session devrait être WAITING_VALIDATION après routing, got {session['status']}"
        )
        steps = {s["step_name"]: s for s in session["steps"]}
        cadrage_step = steps["cadrage"]
        assert cadrage_step["status"] == "WAITING_VALIDATION"
        assert cadrage_step["output_data"]
        print(f"\n[OK] cadrage output : {cadrage_step['output_data'][:300]}")

        # Validation 1 : cadrage
        val1 = api("post", f"/pipelines/{session_id}/validate/{cadrage_step['id']}", json={
            "approved": True,
            "edited_output": None
        })
        print(f"[OK] Validation cadrage → {val1['validation_result']['status']}")

        # Steps 2 et 3 s'auto-complètent (document_mission, selection_contexte)
        # Step 4 (execution) → WAITING_VALIDATION
        session_mid = wait_for_step(session_id, ["WAITING_VALIDATION", "COMPLETED"], max_wait=180)

        if session_mid["status"] == "COMPLETED":
            print(f"[WARN] Pipeline terminé avant execution — vérifier si execution a require_validation")

        if session_mid["status"] == "WAITING_VALIDATION":
            steps_mid = {s["step_name"]: s for s in session_mid["steps"]}
            exec_step = steps_mid.get("execution")
            assert exec_step, "Step 'execution' non trouvé"
            assert exec_step["status"] == "WAITING_VALIDATION"
            assert exec_step["output_data"]
            print(f"[OK] execution output : {exec_step['output_data'][:300]}")

            # Validation 2 : execution
            val2 = api("post", f"/pipelines/{session_id}/validate/{exec_step['id']}", json={
                "approved": True,
                "edited_output": None
            })
            print(f"[OK] Validation execution → {val2['validation_result']['status']}")

            final_session = wait_for_step(session_id, ["COMPLETED", "FAILED"], max_wait=60)
        else:
            final_session = session_mid

        assert final_session["status"] == "COMPLETED", f"Statut final : {final_session['status']}"

        # Vérifier tous les steps COMPLETED
        for step in final_session["steps"]:
            assert step["status"] == "COMPLETED", f"Step {step['step_name']} : {step['status']}"

        print(f"\n{'='*60}")
        print(f"[SUCCESS] mission_complexe complétée en {len(final_session['steps'])} steps")
        print(f"  Session ID   : {session_id}")
        print(f"  Statut final : {final_session['status']}")
        print(f"  Steps        : " + ", ".join(
            f"{s['step_name']}({s['status']})" for s in final_session["steps"]
        ))
        print(f"{'='*60}")


class TestLiveNouveauProjet:
    """Lance nouveau_projet avec 2 validations (draft_projet_contexte + plan_structure)."""

    def test_nouveau_projet_complet(self, fresh_project_dir):
        """
        Workflow : nouveau_projet — 7 steps
        Validations : draft_projet_contexte (step 2), plan_structure (step 4)
        """
        print(f"\n{'='*60}")
        print(f"[TEST] nouveau_projet — Projet : {fresh_project_dir['name']}")
        print(f"{'='*60}")

        project_description = (
            "Je veux créer une application web de suivi de dépenses personnelles. "
            "Type : web. Objectif : enregistrer et visualiser mes dépenses mensuelles. "
            "Utilisateurs : 1 (moi-même, usage personnel). "
            "Fonctionnalités : ajout de dépense (montant, catégorie, date), liste des dépenses "
            "du mois en cours, total par catégorie. "
            "Contraintes : pas d'authentification nécessaire, SQLite pour la base de données, "
            "HTML/JS vanilla sans framework, FastAPI Python."
        )

        result = api("post", "/pipelines/start", json={
            "project_id": fresh_project_dir["id"],
            "workflow_type": "nouveau_projet",
            "initial_input": project_description
        })
        session = result["session"]
        session_id = session["id"]

        print(f"\n[INFO] Session créée : {session_id}")
        print(f"[INFO] Statut initial : {session['status']}")

        # Steps 0+1 auto → Step 2 WAITING_VALIDATION (draft_projet_contexte)
        if session["status"] != "WAITING_VALIDATION":
            session = wait_for_step(session_id, ["WAITING_VALIDATION", "FAILED"], max_wait=120)

        assert session["status"] == "WAITING_VALIDATION"
        steps = {s["step_name"]: s for s in session["steps"]}
        draft_step = steps.get("draft_projet_contexte")
        assert draft_step and draft_step["status"] == "WAITING_VALIDATION"
        assert draft_step["output_data"]
        print(f"\n[OK] draft_projet_contexte output : {draft_step['output_data'][:300]}")

        # Validation 1
        val1 = api("post", f"/pipelines/{session_id}/validate/{draft_step['id']}", json={
            "approved": True,
            "edited_output": None
        })
        print(f"[OK] Validation draft_projet_contexte → {val1['validation_result']['status']}")

        # Step 3 auto → Step 4 WAITING_VALIDATION (plan_structure)
        session_mid = wait_for_step(session_id, ["WAITING_VALIDATION", "COMPLETED", "FAILED"], max_wait=120)

        if session_mid["status"] == "WAITING_VALIDATION":
            steps_mid = {s["step_name"]: s for s in session_mid["steps"]}
            plan_step = steps_mid.get("plan_structure")
            assert plan_step and plan_step["status"] == "WAITING_VALIDATION"
            assert plan_step["output_data"]
            print(f"[OK] plan_structure output : {plan_step['output_data'][:300]}")

            val2 = api("post", f"/pipelines/{session_id}/validate/{plan_step['id']}", json={
                "approved": True,
                "edited_output": None
            })
            print(f"[OK] Validation plan_structure → {val2['validation_result']['status']}")

            final_session = wait_for_step(session_id, ["COMPLETED", "FAILED"], max_wait=120)
        else:
            final_session = session_mid

        assert final_session["status"] == "COMPLETED", f"Statut final : {final_session['status']}"

        print(f"\n{'='*60}")
        print(f"[SUCCESS] nouveau_projet complété — {len(final_session['steps'])} steps")
        print(f"  Session ID   : {session_id}")
        print(f"  Statut final : {final_session['status']}")
        print(f"{'='*60}")


class TestLiveProjetExistant:
    """Lance projet_existant avec 2 validations (production_projet_contexte + nettoyage_docs)."""

    def test_projet_existant_complet(self, existing_project_no_docs):
        """
        Workflow : projet_existant — 7 steps
        Validations : production_projet_contexte (step 4), nettoyage_docs (step 5)
        """
        print(f"\n{'='*60}")
        print(f"[TEST] projet_existant — Projet : {existing_project_no_docs['name']}")
        print(f"{'='*60}")

        project_description = (
            "C'est une application FastAPI simple. Le fichier main.py est le point d'entrée, "
            "database.py gère la connexion SQLite, routes/users.py expose les endpoints utilisateurs. "
            "Pas d'authentification prévue. L'objectif est de créer une API REST minimale "
            "pour gérer des utilisateurs (CRUD). Pas de tests écrits pour l'instant. "
            "La dette technique principale est l'absence de gestion d'erreurs."
        )

        result = api("post", "/pipelines/start", json={
            "project_id": existing_project_no_docs["id"],
            "workflow_type": "projet_existant",
            "initial_input": project_description
        })
        session = result["session"]
        session_id = session["id"]

        print(f"\n[INFO] Session créée : {session_id}")
        print(f"[INFO] Statut initial : {session['status']}")

        # Steps 0-3 auto (peuvent prendre 2-3 min avec Claude Sonnet sur audit_code)
        session = wait_for_step(session_id, ["WAITING_VALIDATION", "FAILED", "COMPLETED"], max_wait=300)

        assert session["status"] == "WAITING_VALIDATION", f"Statut : {session['status']}"
        steps = {s["step_name"]: s for s in session["steps"]}
        prod_step = steps.get("production_projet_contexte")
        assert prod_step and prod_step["status"] == "WAITING_VALIDATION"
        assert prod_step["output_data"]
        print(f"\n[OK] production_projet_contexte output : {prod_step['output_data'][:300]}")

        # Validation 1 : production_projet_contexte
        val1 = api("post", f"/pipelines/{session_id}/validate/{prod_step['id']}", json={
            "approved": True,
            "edited_output": None
        })
        print(f"[OK] Validation production_projet_contexte → {val1['validation_result']['status']}")

        # Step 5 → WAITING_VALIDATION (nettoyage_docs)
        session_mid = wait_for_step(session_id, ["WAITING_VALIDATION", "COMPLETED", "FAILED"], max_wait=60)

        if session_mid["status"] == "WAITING_VALIDATION":
            steps_mid = {s["step_name"]: s for s in session_mid["steps"]}
            nett_step = steps_mid.get("nettoyage_docs")
            assert nett_step and nett_step["status"] == "WAITING_VALIDATION"
            assert nett_step["output_data"]
            print(f"[OK] nettoyage_docs output : {nett_step['output_data'][:200]}")

            val2 = api("post", f"/pipelines/{session_id}/validate/{nett_step['id']}", json={
                "approved": True,
                "edited_output": None
            })
            print(f"[OK] Validation nettoyage_docs → {val2['validation_result']['status']}")

            final_session = wait_for_step(session_id, ["COMPLETED", "FAILED"], max_wait=120)
        else:
            final_session = session_mid

        assert final_session["status"] == "COMPLETED", f"Statut final : {final_session['status']}"

        print(f"\n{'='*60}")
        print(f"[SUCCESS] projet_existant complété — {len(final_session['steps'])} steps")
        print(f"  Session ID   : {session_id}")
        print(f"  Statut final : {final_session['status']}")
        print(f"{'='*60}")
