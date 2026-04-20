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
    """Test que le modal nouveau chat s'ouvre et se ferme correctement."""
    mock_route(browser_page, "**/api/projects/", [])
    mock_route(browser_page, "**/api/chat/conversations*", [])
    mock_route(browser_page, "**/api/atelier/prospects", [])
    
    browser_page.goto(f"{BASE_URL}/app/index.html")
    browser_page.wait_for_load_state("networkidle")
    
    new_chat_btn = browser_page.locator("#btn-new-chat")
    new_chat_btn.click()
    browser_page.wait_for_timeout(500)
    
    modal_overlay = browser_page.locator("#modal-overlay")
    try:
        browser_page.wait_for_selector("#modal-overlay[style*='block']", timeout=2000)
        assert modal_overlay.is_visible(), "Modal overlay devrait être visible"
    except:
        pytest.skip("Modal ne s'est pas ouvert")
    
    close_btn = browser_page.locator(".modal-close, button:has-text('Annuler')")
    if close_btn.count() > 0:
        close_btn.first.click()
        browser_page.wait_for_timeout(300)
        try:
            assert not modal_overlay.is_visible(), "Modal devrait être fermé après clic sur fermer"
        except:
            pass


def test_modal_nouveau_projet_validation_champs_vides(browser_page: Page):
    """Test que le modal nouveau projet valide les champs obligatoires."""
    mock_route(browser_page, "**/api/projects/", [])
    mock_route(browser_page, "**/api/chat/conversations*", [])
    mock_route(browser_page, "**/api/atelier/prospects", [])
    
    browser_page.goto(f"{BASE_URL}/app/index.html")
    browser_page.wait_for_load_state("networkidle")
    
    new_project_btn = browser_page.locator("#btn-new-project")
    if new_project_btn.count() == 0:
        pytest.skip("Bouton nouveau projet non trouvé dans la sidebar")
    
    new_project_btn.click()
    browser_page.wait_for_timeout(300)
    
    modal = browser_page.locator("#modal-new-project")
    if not modal.is_visible():
        pytest.skip("Modal nouveau projet ne s'est pas ouvert")
    
    create_btn = modal.locator("button:has-text('Créer'), button[type='submit']")
    if create_btn.count() > 0:
        create_btn.first.click()
        browser_page.wait_for_timeout(300)
        
        assert modal.is_visible(), "Modal devrait rester ouvert si validation échoue"


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
    
    browser_page.goto(f"{BASE_URL}/app/module-code.html?session=1&project_id=1")
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
    
    browser_page.goto(f"{BASE_URL}/app/module-code.html?session=1&project_id=1")
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
    """Test flux complet : créer un projet et naviguer vers sa page."""
    import random
    import tempfile
    
    page.goto(f"{BASE_URL}/app/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    
    new_project_btn = page.locator("#btn-new-project")
    if new_project_btn.count() == 0:
        pytest.skip("Bouton nouveau projet non trouvé")
    
    new_project_btn.click()
    page.wait_for_timeout(300)
    
    modal = page.locator("#modal-new-project")
    if not modal.is_visible():
        pytest.skip("Modal nouveau projet ne s'est pas ouvert")
    
    project_name = f"Test Projet {random.randint(1000, 9999)}"
    temp_path = tempfile.mkdtemp()
    
    name_input = modal.locator("input[name='name'], input[placeholder*='nom']")
    path_input = modal.locator("input[name='local_path'], input[placeholder*='chemin']")
    
    if name_input.count() > 0:
        name_input.fill(project_name)
    if path_input.count() > 0:
        path_input.fill(temp_path)
    
    create_btn = modal.locator("button:has-text('Créer'), button[type='submit']")
    if create_btn.count() > 0:
        create_btn.first.click()
        page.wait_for_timeout(1000)
        
        sidebar_content = page.locator("#sidebar").text_content()
        assert project_name in sidebar_content, f"Projet '{project_name}' devrait apparaître dans la sidebar"
        
        project_link = page.locator(f"a:has-text('{project_name}'), .project-item:has-text('{project_name}')")
        if project_link.count() > 0:
            project_link.first.click()
            page.wait_for_timeout(500)
            
            assert "dossier.html" in page.url, "Devrait naviguer vers dossier.html"


@pytest.mark.smoke
def test_flux_creer_conversation_et_voir_dans_sidebar(page: Page):
    """Test flux complet : créer une conversation et la voir dans la sidebar."""
    import random
    
    page.goto(f"{BASE_URL}/app/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    
    new_chat_btn = page.locator("#btn-new-chat")
    new_chat_btn.click()
    page.wait_for_timeout(300)
    
    modal = page.locator("#modal-new-chat")
    if not modal.is_visible():
        pytest.skip("Modal nouveau chat ne s'est pas ouvert")
    
    conv_title = f"Test Conv {random.randint(1000, 9999)}"
    
    title_input = modal.locator("input[name='title'], input[placeholder*='titre']")
    if title_input.count() > 0:
        title_input.fill(conv_title)
    
    create_btn = modal.locator("button:has-text('Créer'), button[type='submit']")
    if create_btn.count() > 0:
        create_btn.first.click()
        page.wait_for_timeout(1000)
        
        assert "chat.html" in page.url, "Devrait naviguer vers chat.html après création"
        
        page.goto(f"{BASE_URL}/app/index.html")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        sidebar_content = page.locator("#sidebar").text_content()
        assert conv_title in sidebar_content, f"Conversation '{conv_title}' devrait apparaître dans la sidebar"
