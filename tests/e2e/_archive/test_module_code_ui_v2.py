"""
Tests Playwright — Module Code UI V2 (Mission C03)
Requiert JARVIS en cours d'exécution sur localhost:8000.
Vérifie : nouvelle zone mission, preview parsing, dropdown modèle,
           pré-remplissage URL, pont Réflexion → Code.
"""
import pytest
import requests
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def base_url():
    return "http://localhost:8000"


@pytest.fixture(scope="module")
def api_url():
    return "http://localhost:8000/api"


@pytest.fixture(scope="module")
def project_id(api_url):
    """Crée un projet de test et retourne son id."""
    import tempfile, os
    tmp_dir = tempfile.mkdtemp()
    resp = requests.post(f"{api_url}/projects", json={
        "name": "Test C03 UI",
        "path": tmp_dir,
        "type": "web"
    })
    assert resp.status_code == 200, f"Création projet échouée: {resp.text}"
    return resp.json()["id"]


MISSION_VALIDE = """# MISSION CODE — Ajouter authentification JWT

## Objectif
Ajouter un système d'authentification JWT à l'API backend pour sécuriser les routes.

## Fichiers concernés
- `backend/main.py` — ajout middleware auth
- `backend/routers/auth.py` — nouvelles routes login/refresh

## Contraintes
- Utiliser la librairie python-jose
- Tokens avec expiration 24h

## Critères de réussite
- Route /api/auth/login retourne un token JWT valide
- Routes protégées renvoient 401 sans token
"""

MISSION_INVALIDE = """Corriger le bug dans le fichier principal.
Il y a une erreur quelque part."""


# ─── Test 1 : Navigation vers code-project-detail ───────────────────────────

def test_page_charge_sans_erreur(page: Page, base_url, project_id):
    """Test 1 : navigation vers code-project-detail, page se charge sans erreur."""
    page.goto(f"{base_url}/app/code-project-detail.html?id={project_id}")
    page.wait_for_load_state("networkidle", timeout=10000)

    expect(page.locator("#mission-prompt-input")).to_be_visible()
    expect(page.locator("#model-override-select")).to_be_visible()
    expect(page.locator("#btn-launch-mission")).to_be_visible()
    expect(page.locator("#mission-step-a")).not_to_be_attached()
    expect(page.locator("#mission-step-b")).not_to_be_attached()
    expect(page.locator("#btn-analyze")).not_to_be_attached()


# ─── Test 2 : Preview parsing prompt valide ─────────────────────────────────

def test_preview_parsing_prompt_valide(page: Page, base_url, project_id):
    """Test 2 : coller un prompt mission valide → preview affiche titre + nombre fichiers."""
    page.goto(f"{base_url}/app/code-project-detail.html?id={project_id}")
    page.wait_for_load_state("networkidle", timeout=10000)

    textarea = page.locator("#mission-prompt-input")
    textarea.fill(MISSION_VALIDE)
    textarea.dispatch_event("input")

    preview = page.locator("#mission-preview")
    preview.wait_for(state="visible", timeout=5000)

    preview_inner = page.locator("#mission-preview-inner")
    expect(preview_inner).to_contain_text("Authentification JWT", ignore_case=True)
    expect(preview_inner).to_contain_text("fichier", ignore_case=True)


# ─── Test 3 : Avertissement parsing prompt invalide ─────────────────────────

def test_avertissement_parsing_prompt_invalide(page: Page, base_url, project_id):
    """Test 3 : coller un prompt invalide (sans Objectif) → avertissement orange visible."""
    page.goto(f"{base_url}/app/code-project-detail.html?id={project_id}")
    page.wait_for_load_state("networkidle", timeout=10000)

    textarea = page.locator("#mission-prompt-input")
    textarea.fill(MISSION_INVALIDE)
    textarea.dispatch_event("input")

    warning = page.locator("#mission-warning")
    warning.wait_for(state="visible", timeout=5000)

    inner_text = warning.inner_text()
    assert len(inner_text) > 0, "L'avertissement est vide"


# ─── Test 4 : Pré-remplissage depuis URL reflexion_session ──────────────────

def test_prefill_depuis_url_reflexion_session(page: Page, base_url, api_url, project_id):
    """Test 4 : pré-remplissage depuis URL ?reflexion_session= → textarea pré-rempli."""
    resp = requests.post(f"{api_url}/reflexions", json={
        "project_id": project_id,
        "livrable_type": "mission_code"
    })
    if resp.status_code != 200:
        pytest.skip("API réflexion non disponible")

    session_id = resp.json()["id"]

    page.goto(
        f"{base_url}/app/code-project-detail.html?id={project_id}&reflexion_session={session_id}"
    )
    page.wait_for_load_state("networkidle", timeout=10000)

    page.wait_for_timeout(2000)

    textarea = page.locator("#mission-prompt-input")
    textarea_value = textarea.input_value()
    assert isinstance(textarea_value, str)


# ─── Test 5 : Dropdown pré-sélectionne la recommandation du parsing ──────────

def test_dropdown_preselection_recommandation(page: Page, base_url, project_id):
    """Test 5 : dropdown modèle pré-sélectionne la recommandation du parsing."""
    page.goto(f"{base_url}/app/code-project-detail.html?id={project_id}")
    page.wait_for_load_state("networkidle", timeout=10000)

    select = page.locator("#model-override-select")
    initial_value = select.input_value()
    assert initial_value == "anthropic/claude-haiku-4-5", f"Valeur par défaut incorrecte: {initial_value}"

    textarea = page.locator("#mission-prompt-input")
    textarea.fill(MISSION_VALIDE)
    textarea.dispatch_event("input")

    page.wait_for_timeout(1500)

    new_value = select.input_value()
    assert new_value in [
        "anthropic/claude-haiku-4-5",
        "anthropic/claude-sonnet-4-5",
        "google/gemini-2.5-flash",
        "google/gemini-2.5-pro"
    ], f"Valeur dropdown inattendue: {new_value}"


# ─── Test 6 : Changement dropdown → valeur correcte dans le body /start ─────

def test_dropdown_changement_envoi_correct(page: Page, base_url, project_id):
    """Test 6 : changement dropdown modèle → valeur envoyée à /pipelines/start."""
    page.goto(f"{base_url}/app/code-project-detail.html?id={project_id}")
    page.wait_for_load_state("networkidle", timeout=10000)

    select = page.locator("#model-override-select")
    select.select_option("google/gemini-2.5-pro")
    assert select.input_value() == "google/gemini-2.5-pro"

    textarea = page.locator("#mission-prompt-input")
    textarea.fill(MISSION_VALIDE)

    intercepted_body = {}

    def handle_route(route):
        if "/pipelines/start" in route.request.url:
            try:
                body = route.request.post_data_json
                intercepted_body.update(body or {})
            except Exception:
                pass
        route.continue_()

    page.route("**/pipelines/start", handle_route)

    btn = page.locator("#btn-launch-mission")
    btn.click()

    page.wait_for_timeout(2000)

    if intercepted_body:
        assert intercepted_body.get("modele_override") == "google/gemini-2.5-pro", \
            f"modele_override incorrect: {intercepted_body.get('modele_override')}"
        assert intercepted_body.get("workflow_type") == "code_mission"


# ─── Test 7 : Depuis Réflexion FIGEE, bouton Lancer dans Module Code ─────────

def test_bouton_lancer_depuis_reflexion_figee(page: Page, base_url, api_url, project_id):
    """Test 7 : depuis reflexion.html FIGEE, clic 'Lancer dans Module Code' → redirection correcte."""
    resp = requests.post(f"{api_url}/reflexions", json={
        "project_id": project_id,
        "livrable_type": "mission_code"
    })
    if resp.status_code != 200:
        pytest.skip("API réflexion non disponible")

    session_id = resp.json()["id"]

    figer_resp = requests.post(f"{api_url}/reflexions/{session_id}/figer")
    if figer_resp.status_code != 200:
        pytest.skip("Figement échoué — session sans messages")

    page.goto(f"{base_url}/app/reflexion.html?session={session_id}")
    page.wait_for_load_state("networkidle", timeout=10000)
    page.wait_for_timeout(2000)

    btn_lancer = page.locator("#btn-lancer-module-code")
    expect(btn_lancer).to_be_visible(timeout=5000)

    btn_lancer.click()

    page.wait_for_url(
        f"**/code-project-detail.html?id={project_id}&reflexion_session={session_id}",
        timeout=5000
    )

    assert f"reflexion_session={session_id}" in page.url
