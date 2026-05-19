"""
Fixtures et helpers partagés pour les tests live JARVIS Orchestrateur.
Prérequis : serveur actif sur localhost:8000
"""
import pytest
import httpx
import uuid

BASE = "http://localhost:8000/api"
TIMEOUT = 120.0


def jarvis_api(method: str, path: str, **kwargs) -> dict:
    """Appelle l'API JARVIS locale. Lève AssertionError si status >= 400."""
    url = f"{BASE}{path}"
    r = getattr(httpx, method)(url, timeout=TIMEOUT, **kwargs)
    assert r.status_code < 400, (
        f"{method.upper()} {path} → {r.status_code}\n{r.text[:500]}"
    )
    return r.json()


def chat(conv_id: int, message: str, force_agent: str = None) -> dict:
    """Envoie un message dans une conversation JARVIS. Retourne la réponse complète."""
    payload = {"message": message}
    if force_agent:
        payload["force_agent"] = force_agent
    return jarvis_api("post", f"/jarvis/conversations/{conv_id}/chat", json=payload)


def assert_valid_response(res: dict, expected_agents: list = None):
    """Vérifie qu'une réponse JARVIS est structurellement valide."""
    assert "agent" in res, "Champ 'agent' absent"
    assert "content" in res, "Champ 'content' absent"
    assert res["content"], "Réponse vide"
    assert len(res["content"]) > 10, f"Réponse trop courte : {res['content']!r}"
    if expected_agents:
        assert res["agent"] in expected_agents, (
            f"Agent inattendu : {res['agent']} (attendu : {expected_agents})"
        )


@pytest.fixture
def conv():
    """
    Crée une conversation JARVIS de test, yield son id, puis la supprime.
    Usage : def test_xxx(conv): chat(conv, "message")
    """
    c = jarvis_api("post", "/jarvis/conversations", json={"title": "TEST_LIVE_AUTO"})
    conv_id = c["id"]
    yield conv_id
    try:
        jarvis_api("delete", f"/jarvis/conversations/{conv_id}")
    except Exception:
        pass  # Nettoyage best-effort


@pytest.fixture
def conv_with_project(tmp_path):
    """
    Conversation liée à un projet de test avec fichiers réels sur le disque.
    Utilisé par les tests MENTOR/FORGE.
    """
    # Le chemin sera créé par l'API (module_type='code' crée le dossier)
    project_dir = tmp_path / "test_projet_live"
    unique_name = f"Test Live Project {uuid.uuid4().hex[:8]}"

    # Enregistrer en DB — l'API crée le dossier sur le disque
    proj = jarvis_api("post", "/projects", json={
        "name": unique_name,
        "path": str(project_dir),
        "type": "code",
        "module_type": "code",
    })

    # Écrire les fichiers de test dans le dossier créé par l'API
    (project_dir / "main.py").write_text(
        "def hello():\n    return 'hello world'\n"
    )
    (project_dir / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n"
    )
    project_id = proj["id"]

    # Créer une conversation liée à ce projet
    c = jarvis_api("post", "/jarvis/conversations", json={
        "title": "TEST_LIVE_MENTOR_FORGE",
        "project_id": project_id,
    })
    conv_id = c["id"]

    yield {"conv_id": conv_id, "project_id": project_id, "project_dir": project_dir}

    # Cleanup
    try:
        jarvis_api("delete", f"/jarvis/conversations/{conv_id}")
    except Exception:
        pass
    try:
        jarvis_api("delete", f"/projects/{project_id}")
    except Exception:
        pass
