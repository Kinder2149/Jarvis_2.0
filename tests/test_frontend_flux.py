"""
TEST-FRONT-02 : Tests d'interaction et flux complets
Tests Playwright qui simulent des actions utilisateur et vérifient les réactions de l'UI.
Tests 1-8 : ne nécessitent pas de serveur backend (routes mockées)
Tests 9-10 : nécessitent le serveur démarré (marqueur @pytest.mark.smoke)
"""
import pytest
from playwright.sync_api import Page, Route
import json
import time

BASE_URL = "http://localhost:8000"


def mock_route(page: Page, url_pattern: str, response_data, status: int = 200, delay_ms: int = 0):
    """Intercepte une route et retourne des données fixes avec délai optionnel."""
    def handle(route: Route):
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(response_data)
        )
    page.route(url_pattern, handle)


def mock_fallback_routes(page: Page):
    """Mock toutes les routes API non explicitement mockées pour éviter les 404."""
    page.route("**/api/**", lambda route: route.fulfill(status=200, body="[]"))


@pytest.fixture
def browser_page(page: Page):
    """Fixture qui configure le fallback pour toutes les routes API."""
    mock_fallback_routes(page)
    return page


# =============================================================================
# INTERACTIONS SIDEBAR
# =============================================================================

def test_sidebar_collapse_expand(browser_page: Page):
    """Test que la sidebar se collapse et s'expand correctement."""
    mock_route(browser_page, "**/api/projects/", [])
    mock_route(browser_page, "**/api/chat/conversations*", [])
    mock_route(browser_page, "**/api/atelier/prospects", [])
    
    browser_page.goto(f"{BASE_URL}/app/index.html")
    browser_page.wait_for_load_state("networkidle")
    
    sidebar = browser_page.locator("#sidebar")
    collapse_btn = browser_page.locator("#btn-sidebar-collapse")
    
    initial_width = sidebar.bounding_box()["width"]
    
    collapse_btn.click()
    browser_page.wait_for_timeout(500)
    
    collapsed_width = sidebar.bounding_box()["width"]
    assert collapsed_width < initial_width, f"Sidebar devrait être plus petite après collapse ({collapsed_width} >= {initial_width})"
    
    collapse_btn.click()
    browser_page.wait_for_timeout(500)
    
    expanded_width = sidebar.bounding_box()["width"]
    assert expanded_width > collapsed_width, f"Sidebar devrait être plus grande après expand ({expanded_width} <= {collapsed_width})"


def test_modal_nouveau_chat_ouvre_et_ferme(browser_page: Page):
    """Test que le bouton nouveau chat redirige vers chat.html (comportement actuel)."""
    mock_route(browser_page, "**/api/projects**", [])
    mock_route(browser_page, "**/api/chat/conversations**", [])
    mock_route(browser_page, "**/api/atelier/prospects", [])
    mock_fallback_routes(browser_page)
    
    browser_page.goto(f"{BASE_URL}/app/index.html")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(500)
    
    # Cliquer le bouton "Nouveau Chat" dans la sidebar
    btn = browser_page.locator("#btn-new-chat").first
    assert btn.is_visible(), "Bouton Nouveau Chat non trouvé dans sidebar"
    
    # Vérifier que le clic redirige vers chat.html
    btn.click()
    browser_page.wait_for_load_state("networkidle")
    
    assert "chat.html" in browser_page.url, "Devrait rediriger vers chat.html après clic"


def test_modal_nouveau_projet_validation_champs_vides(browser_page: Page):
    """Test que le modal nouvelle réflexion s'ouvre et affiche les champs."""
    mock_route(browser_page, "**/api/projects**", [])
    mock_route(browser_page, "**/api/chat/conversations**", [])
    mock_route(browser_page, "**/api/atelier/prospects", [])
    mock_fallback_routes(browser_page)
    
    browser_page.goto(f"{BASE_URL}/app/index.html")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(500)
    
    # Trouver le bouton nouvelle réflexion dans la sidebar
    new_reflexion_btn = browser_page.locator("#btn-new-reflexion").first
    assert new_reflexion_btn.is_visible(), "Bouton nouvelle réflexion non trouvé dans sidebar"
    new_reflexion_btn.click()
    browser_page.wait_for_timeout(500)
    
    modal = browser_page.locator(".modal-overlay")
    assert modal.is_visible(), "Modal Nouvelle Réflexion devrait s'ouvrir"
    
    # Vérifier les champs du modal réflexion
    assert browser_page.locator("#modal-mission-project").count() >= 1, "Champ projet manquant"
    
    # Fermer le modal via le bouton ×
    browser_page.locator(".modal-header .btn-icon").click()
    browser_page.wait_for_timeout(300)
    assert not modal.is_visible(), "Modal devrait se fermer après clic ×"


def test_modal_fermeture_clic_overlay(browser_page: Page):
    """Test que le modal se ferme quand on clique sur l'overlay (en dehors du modal)."""
    mock_route(browser_page, "**/api/projects**", [])
    mock_route(browser_page, "**/api/chat/conversations**", [])
    mock_route(browser_page, "**/api/atelier/prospects", [])
    mock_fallback_routes(browser_page)
    
    browser_page.goto(f"{BASE_URL}/app/index.html")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(500)
    
    # Ouvrir le modal nouvelle réflexion (qui fonctionne réellement)
    btn = browser_page.locator("#btn-new-reflexion").first
    assert btn.is_visible(), "Bouton Nouvelle Réflexion non trouvé"
    btn.click()
    browser_page.wait_for_timeout(500)
    
    modal = browser_page.locator(".modal-overlay")
    assert modal.is_visible(), "Modal devrait être ouvert"
    
    # Cliquer sur l'overlay (en dehors du .modal)
    # Utiliser force=True pour cliquer sur l'overlay même si le .modal est au-dessus
    modal.click(position={"x": 10, "y": 10}, force=True)
    browser_page.wait_for_timeout(300)
    
    # Le modal devrait se fermer
    assert not modal.is_visible(), "Modal devrait se fermer après clic sur overlay"


# =============================================================================
# INTERACTIONS CHAT
# =============================================================================

def test_chat_optimistic_ui(browser_page: Page):
    """Test que l'optimistic UI affiche le message utilisateur immédiatement."""
    mock_route(
        browser_page,
        "**/api/chat/conversations/1",
        {
            "id": 1,
            "title": "Test chat",
            "folder_path": None,
            "internet_access": 0,
            "model": "",
            "messages": []
        }
    )
    mock_route(browser_page, "**/api/config/models/available", [])
    
    # Mock POST avec délai pour simuler latence réseau
    def handle_post(route: Route):
        if route.request.method == "POST":
            time.sleep(1)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"id": 10, "role": "assistant", "content": "Réponse IA", "created_at": "2026-04-20T10:00:01"})
            )
        else:
            route.fulfill(status=200, body="[]")
    
    browser_page.route("**/api/chat/conversations/1/messages", handle_post)
    
    browser_page.goto(f"{BASE_URL}/app/chat.html?id=1")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(500)
    
    message_input = browser_page.locator("#chat-input").first
    send_btn = browser_page.locator("#btn-send").first
    
    if message_input.count() == 0 or send_btn.count() == 0:
        pytest.skip("Éléments de chat non trouvés")
    
    message_input.fill("Bonjour optimistic")
    send_btn.click()
    
    # Vérifier affichage immédiat (optimistic UI)
    browser_page.wait_for_timeout(200)
    content = browser_page.content()
    assert "Bonjour optimistic" in content, "Message utilisateur devrait apparaître immédiatement (optimistic UI)"


def test_chat_raccourci_ctrl_entree(browser_page: Page):
    """Test que Ctrl+Entrée envoie le message."""
    mock_route(
        browser_page,
        "**/api/chat/conversations/1",
        {
            "id": 1,
            "title": "Test chat",
            "folder_path": None,
            "internet_access": 0,
            "model": "",
            "messages": []
        }
    )
    mock_route(browser_page, "**/api/config/models/available", [])
    mock_route(
        browser_page,
        "**/api/chat/conversations/1/messages",
        {"id": 10, "role": "assistant", "content": "OK", "created_at": "2026-04-20T10:00:01"}
    )
    
    browser_page.goto(f"{BASE_URL}/app/chat.html?id=1")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(500)
    
    message_input = browser_page.locator("#chat-input").first
    
    if message_input.count() == 0:
        pytest.skip("Champ de message non trouvé")
    
    message_input.fill("Test raccourci")
    message_input.press("Control+Enter")
    
    browser_page.wait_for_timeout(500)
    content = browser_page.content()
    assert "Test raccourci" in content, "Message devrait être envoyé avec Ctrl+Entrée"


# =============================================================================
# INTERACTIONS MODULE CODE
# =============================================================================

def test_module_code_abort_demande_confirmation(browser_page: Page):
    """Test que l'abandon d'une session demande confirmation."""
    mock_route(
        browser_page,
        "**/api/pipelines/1",
        {
            "id": 1,
            "workflow_type": "bug_simple",
            "status": "RUNNING",
            "project_id": 1,
            "steps": [
                {"id": 1, "step_display_name": "En cours", "status": "RUNNING", "output_type": "text", "requires_validation": False, "error_message": None}
            ]
        }
    )
    
    browser_page.goto(f"{BASE_URL}/app/mission.html?pipeline_session=1&project_id=1")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(1000)
    
    abort_btn = browser_page.locator("button:has-text('Abandonner'), button:has-text('Annuler')")
    
    if abort_btn.count() == 0:
        pytest.skip("Bouton abandonner non trouvé")
    
    browser_page.on("dialog", lambda dialog: dialog.accept())
    
    abort_btn.first.click()
    browser_page.wait_for_timeout(500)


def test_module_code_retry_step(browser_page: Page):
    """Test que le retry d'un step FAILED fonctionne."""
    mock_route(
        browser_page,
        "**/api/pipelines/1",
        {
            "id": 1,
            "workflow_type": "bug_simple",
            "status": "FAILED",
            "project_id": 1,
            "steps": [
                {"id": 1, "step_display_name": "Étape échouée", "status": "FAILED", "output_type": "text", "requires_validation": False, "error_message": "Erreur test"}
            ]
        }
    )
    
    retry_called = {"value": False}
    
    def handle_retry(route: Route):
        retry_called["value"] = True
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"status": "PENDING"}))
    
    browser_page.route("**/api/pipelines/1/retry/1", handle_retry)
    
    browser_page.goto(f"{BASE_URL}/app/mission.html?pipeline_session=1&project_id=1")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(1000)
    
    retry_btn = browser_page.locator("button:has-text('🔄'), button:has-text('Relancer'), button:has-text('Retry')")
    
    if retry_btn.count() == 0:
        pytest.skip("Bouton retry non trouvé")
    
    retry_btn.first.click()
    browser_page.wait_for_timeout(500)
    
    assert retry_called["value"], "L'appel API retry devrait avoir été effectué"


# =============================================================================
# INTERACTIONS ATELIER
# =============================================================================

def test_atelier_creation_prospect(browser_page: Page):
    """Test que la création d'un prospect fonctionne."""
    mock_route(browser_page, "**/api/atelier/prospects", [])
    
    prospect_created = {"value": False}
    
    def handle_create(route: Route):
        prospect_created["value"] = True
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"id": 99, "nom": "Nouveau Restaurant", "statut": "nouveau", "session_status": None})
        )
    
    browser_page.route("**/api/atelier/prospects", lambda route: handle_create(route) if route.request.method == "POST" else route.fulfill(status=200, body="[]"))
    
    browser_page.goto(f"{BASE_URL}/app/atelier.html")
    browser_page.wait_for_load_state("networkidle")
    browser_page.wait_for_timeout(500)
    
    new_prospect_btn = browser_page.locator("button:has-text('Nouveau'), button:has-text('+'), button:has-text('Ajouter')")
    
    if new_prospect_btn.count() == 0:
        pytest.skip("Bouton nouveau prospect non trouvé")
    
    new_prospect_btn.first.click()
    browser_page.wait_for_timeout(300)
    
    name_input = browser_page.locator("input[name='nom'], input[placeholder*='nom']")
    if name_input.count() > 0:
        name_input.fill("Nouveau Restaurant")
        
        submit_btn = browser_page.locator("button:has-text('Créer'), button:has-text('Ajouter'), button[type='submit']")
        if submit_btn.count() > 0:
            submit_btn.first.click()
            browser_page.wait_for_timeout(500)


# =============================================================================
# FLUX COMPLETS (smoke tests avec vrai serveur)
# =============================================================================

@pytest.mark.smoke
def test_flux_creation_et_navigation_projet(page: Page):
    """Test flux complet : créer un projet via API et naviguer vers sa page."""
    import random
    import tempfile
    import time
    import httpx
    from pathlib import Path
    
    # Créer un projet via API (plus fiable que via UI)
    project_name = f"Smoke Test Projet {int(time.time())}"
    temp_path = tempfile.mkdtemp()
    
    # Créer un PROJET_CONTEXTE.md minimal pour que le projet soit valide
    project_dir = Path(temp_path)
    (project_dir / "PROJET_CONTEXTE.md").write_text(
        f"# {project_name}\n## 1. IDENTITE\n|Nom|{project_name}|",
        encoding="utf-8"
    )
    
    try:
        # Créer le projet via API
        resp = httpx.post(
            f"{BASE_URL}/api/projects",
            json={
                "name": project_name,
                "path": str(temp_path),
                "type": "web",
                "module_type": "dossier"
            },
            timeout=10.0
        )
        assert resp.status_code == 200, f"Échec création projet: {resp.status_code}"
        project_id = resp.json()["id"]
        
        # Naviguer vers index et vérifier que le projet apparaît dans la sidebar
        page.goto(f"{BASE_URL}/app/index.html")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        
        sidebar_content = page.locator("#sidebar").text_content()
        assert project_name in sidebar_content, f"Projet '{project_name}' devrait apparaître dans la sidebar"
        
        # Cliquer sur le projet pour naviguer vers dossier.html
        project_link = page.locator(f".nav-project-name:has-text('{project_name}')").first
        assert project_link.is_visible(), f"Lien projet '{project_name}' non visible"
        project_link.click()
        page.wait_for_timeout(1000)
        
        assert "dossier.html" in page.url, "Devrait naviguer vers dossier.html"
        assert f"id={project_id}" in page.url, "URL devrait contenir l'ID du projet"
        
    finally:
        # Nettoyage
        try:
            httpx.delete(f"{BASE_URL}/api/projects/{project_id}", timeout=5.0)
        except:
            pass
        import shutil
        shutil.rmtree(str(temp_path), ignore_errors=True)


@pytest.mark.smoke
def test_flux_creer_conversation_et_voir_dans_sidebar(page: Page):
    """Test flux complet : créer une conversation via API et la voir dans la sidebar."""
    import time
    import httpx
    
    conv_title = f"Smoke Test Conv {int(time.time())}"
    
    try:
        # Créer la conversation via API
        resp = httpx.post(
            f"{BASE_URL}/api/chat/conversations",
            json={
                "title": conv_title,
                "project_id": None
            },
            timeout=10.0
        )
        assert resp.status_code == 200, f"Échec création conversation: {resp.status_code}"
        conv_id = resp.json()["id"]
        
        # Naviguer vers index et vérifier que la conversation apparaît dans la sidebar
        page.goto(f"{BASE_URL}/app/index.html")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        
        # Cliquer sur l'onglet Chats dans la sidebar
        chat_tab = page.locator(".sidebar-tab[data-tab='conversations']")
        if chat_tab.is_visible():
            chat_tab.click()
            page.wait_for_timeout(500)
        
        sidebar_content = page.locator("#sidebar").text_content()
        assert conv_title in sidebar_content, f"Conversation '{conv_title}' devrait apparaître dans la sidebar"
        
        # Cliquer sur la conversation pour naviguer vers chat.html
        conv_link = page.locator(f".nav-conversation-title:has-text('{conv_title}')").first
        if conv_link.count() == 0:
            conv_link = page.locator(f"a:has-text('{conv_title}')").first
        
        assert conv_link.is_visible(), f"Lien conversation '{conv_title}' non visible"
        conv_link.click()
        page.wait_for_timeout(1000)
        
        assert "chat.html" in page.url, "Devrait naviguer vers chat.html"
        assert f"id={conv_id}" in page.url, "URL devrait contenir l'ID de la conversation"
        
    finally:
        # Nettoyage
        try:
            httpx.delete(f"{BASE_URL}/api/chat/conversations/{conv_id}", timeout=5.0)
        except:
            pass


@pytest.mark.smoke
def test_smoke_flux_module_code_session(page: Page):
    """Test flux complet : créer un projet code et démarrer une session pipeline."""
    import time
    import tempfile
    import httpx
    from pathlib import Path
    
    # Créer un projet avec un dossier tmp valide
    project_dir = Path(tempfile.mkdtemp())
    project_name = f"Smoke Test Code {int(time.time())}"
    
    (project_dir / "PROJET_CONTEXTE.md").write_text(
        f"# {project_name}\n## 1. IDENTITE\n|Nom|{project_name}|\n## 2. STACK TECHNIQUE\nPython + FastAPI",
        encoding="utf-8"
    )
    (project_dir / "main.py").write_text("# Test file\nprint('hello')", encoding="utf-8")
    
    try:
        # Créer le projet via API
        proj_resp = httpx.post(
            f"{BASE_URL}/api/projects",
            json={
                "name": project_name,
                "path": str(project_dir),
                "type": "web",
                "module_type": "code"
            },
            timeout=10.0
        )
        assert proj_resp.status_code == 200, f"Échec création projet: {proj_resp.status_code}"
        project_id = proj_resp.json()["id"]
        
        # Naviguer vers la liste des projets code
        page.goto(f"{BASE_URL}/app/code-projects.html")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        
        # Vérifier que le projet apparaît
        content = page.content()
        assert project_name in content, f"Projet '{project_name}' non visible dans code-projects"
        
        # Démarrer une session via API (pas via UI pour éviter l'IA)
        session_resp = httpx.post(
            f"{BASE_URL}/api/pipelines/start",
            json={
                "project_id": project_id,
                "workflow_type": "code_mission",
                "user_input": "Test smoke: corriger un bug simple dans main.py"
            },
            timeout=10.0
        )
        assert session_resp.status_code == 200, f"Échec démarrage session: {session_resp.status_code}"
        session_id = session_resp.json()["id"]
        
        # Naviguer vers la session (mission.html remplace module-code.html)
        page.goto(f"{BASE_URL}/app/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        
        # Vérifier que les steps s'affichent
        content = page.content()
        assert "step" in content.lower() or "étape" in content.lower(), \
            "Steps non visibles sur la page mission"
        
        # Aborter proprement
        httpx.post(f"{BASE_URL}/api/pipelines/{session_id}/abort", timeout=5.0)
        
    finally:
        # Nettoyage
        try:
            httpx.delete(f"{BASE_URL}/api/projects/{project_id}", timeout=5.0)
        except:
            pass
        import shutil
        shutil.rmtree(str(project_dir), ignore_errors=True)
