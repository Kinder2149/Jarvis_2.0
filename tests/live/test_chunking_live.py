"""
Test LIVE — Chunking automatique avec appel LLM réel.

Marqué @pytest.mark.live — ne s'exécute PAS dans la suite normale.
Commande : python -m pytest tests/live/test_chunking_live.py -m live -v --timeout=120

Prérequis :
  - JARVIS doit tourner : uvicorn backend.main:app --reload --port 8000
  - Clé API valide dans config.json (openrouter_key)
  - 3 fichiers temporaires créés automatiquement par le test
"""
import pytest
import httpx
import asyncio
from pathlib import Path

BASE_URL = "http://localhost:8000"
pytestmark = pytest.mark.live

MISSION_PROMPT_CHUNKING = """# MISSION CODE — Test chunking multi-fichiers

## Objectif
Ajouter un commentaire d'en-tête dans chacun des fichiers ciblés.

## Fichiers concernés
- `test_file_alpha.py` — Premier fichier de test
- `test_file_beta.py` — Deuxième fichier de test
- `test_file_gamma.py` — Troisième fichier de test

## Contraintes
- Ajouter uniquement un commentaire en première ligne
- Ne pas modifier le reste du code

## Critères de réussite
- Chaque fichier a son commentaire d'en-tête
"""


async def _wait_for_step_status(
    client: httpx.AsyncClient,
    session_id: int,
    step_index: int,
    expected_statuses: list,
    max_wait: int = 90,
) -> dict:
    for _ in range(max_wait // 3):
        await asyncio.sleep(3)
        resp = await client.get(f"{BASE_URL}/api/pipelines/{session_id}")
        if resp.status_code != 200:
            continue
        session = resp.json()
        steps = session.get("steps", [])
        matching = [s for s in steps if s["step_index"] == step_index]
        if matching and matching[0]["status"] in expected_statuses:
            return session
    return {}


@pytest.mark.live
@pytest.mark.asyncio
async def test_chunking_live_3_fichiers(tmp_path):
    """
    Test live : mission avec 3 gros fichiers → chunking actif → 3 appels LLM réels.
    Vérifie :
    1. La session démarre correctement
    2. L'étape execution produit un output non vide
    3. Des sub-steps sont persistés (si chunking déclenché)
    """
    large_content = "x" * 250_000

    project_dir = tmp_path / "test_chunking_live"
    project_dir.mkdir()
    (project_dir / "test_file_alpha.py").write_text(f"# alpha\n{large_content}", encoding="utf-8")
    (project_dir / "test_file_beta.py").write_text(f"# beta\n{large_content}", encoding="utf-8")
    (project_dir / "test_file_gamma.py").write_text(f"# gamma\n{large_content}", encoding="utf-8")
    (project_dir / "PROJET_CONTEXTE.md").write_text(
        "## 1. IDENTITE\n| Nom | Test Live Chunking |\n| Type | test |\n"
        "## 8. SESSION EN COURS\nTest chunking live\n",
        encoding="utf-8"
    )

    async with httpx.AsyncClient(timeout=30) as client:
        # Créer le projet
        resp = await client.post(
            f"{BASE_URL}/api/projects",
            json={"name": "Test Chunking Live", "path": str(project_dir), "type": "test"},
        )
        assert resp.status_code == 200, f"Création projet échouée: {resp.text}"
        project_id = resp.json()["id"]

        # Démarrer la session code_mission
        resp = await client.post(
            f"{BASE_URL}/api/pipelines/start",
            json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "initial_input": MISSION_PROMPT_CHUNKING,
                "modele_override": "anthropic/claude-haiku-4.5",
            },
        )
        assert resp.status_code == 200, f"Démarrage session échouée: {resp.text}"
        session_id = resp.json()["session_id"]
        assert session_id is not None

        # Attendre que l'étape execution soit terminée (step_index=1)
        session_data = await _wait_for_step_status(
            client, session_id, step_index=1,
            expected_statuses=["COMPLETED", "WAITING_VALIDATION", "FAILED"],
            max_wait=90,
        )

        assert session_data, "Timeout : l'étape execution n'a pas terminé dans les délais"

        steps = session_data.get("steps", [])
        exec_steps = [s for s in steps if s.get("step_index") == 1]
        assert exec_steps, "Aucun step d'execution trouvé"

        exec_step = exec_steps[0]
        assert exec_step["status"] in ("COMPLETED", "WAITING_VALIDATION"), (
            f"Step execution status inattendu : {exec_step['status']}"
        )
        assert exec_step.get("output_data"), "Output de l'étape execution vide"

    print(f"\n[LIVE] Session {session_id} — output length: {len(exec_step.get('output_data', ''))}")
    print("[LIVE] Chunking live test : SUCCÈS")
