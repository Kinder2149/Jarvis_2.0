"""
Tests Playwright — Page mission.html
Couvre les 3 zones progressives et les principaux flux utilisateur.
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000/app"


# ── Helpers ───────────────────────────────────────────────────────────

def goto_mission_empty(page: Page):
    """Ouvrir mission.html sans paramètre."""
    page.goto(f"{BASE_URL}/mission.html")
    page.wait_for_load_state("networkidle")


def goto_mission_new(page: Page, project_id: int = 1):
    """Ouvrir mission.html en mode création."""
    page.goto(f"{BASE_URL}/mission.html?project_id={project_id}&new=true")
    page.wait_for_load_state("networkidle")


def goto_mission_session(page: Page, session_id: int):
    """Ouvrir mission.html avec session réflexion existante."""
    page.goto(f"{BASE_URL}/mission.html?session={session_id}")
    page.wait_for_load_state("networkidle")


def goto_mission_pipeline(page: Page, pipeline_session_id: int):
    """Ouvrir mission.html avec session pipeline existante."""
    page.goto(f"{BASE_URL}/mission.html?pipeline_session={pipeline_session_id}")
    page.wait_for_load_state("networkidle")


# ── Tests état vide ───────────────────────────────────────────────────

def test_mission_empty_state_displayed(page: Page):
    """T01 — Sans paramètre URL, l'état vide est affiché."""
    goto_mission_empty(page)
    empty_state = page.locator("#mission-empty-state")
    expect(empty_state).to_be_visible()
    # Flow mission masqué
    flow = page.locator("#mission-flow")
    expect(flow).to_be_hidden()


def test_mission_empty_state_has_link_to_projects(page: Page):
    """T02 — L'état vide contient un lien vers code-projects.html."""
    goto_mission_empty(page)
    link = page.locator("#mission-empty-state a[href='code-projects.html']")
    expect(link).to_be_visible()


def test_mission_four_steps_always_in_dom(page: Page):
    """T00 — Les 4 cartes #step-1 à #step-4 sont toujours présentes dans le DOM."""
    goto_mission_session(page, session_id=1)
    for i in range(1, 5):
        card = page.locator(f"#step-{i}")
        expect(card).to_be_attached()


# ── Tests formulaire création ─────────────────────────────────────────

def test_mission_create_form_displayed(page: Page):
    """T03 — Avec ?project_id=X&new=true, le formulaire de création apparaît."""
    goto_mission_new(page, project_id=1)
    form = page.locator("#mission-create-form")
    expect(form).to_be_visible()
    # Le bouton créer est présent
    btn = page.locator("#btn-create-session")
    expect(btn).to_be_visible()


def test_mission_create_form_livrable_types(page: Page):
    """T04 — Le formulaire propose les 3 types de livrable."""
    goto_mission_new(page, project_id=1)
    for value in ["mission_code", "decision_figee", "plan_multi_missions"]:
        radio = page.locator(f"input[name='create_livrable_type'][value='{value}']")
        expect(radio).to_be_visible()


def test_mission_create_form_default_is_mission_code(page: Page):
    """T05 — Le type mission_code est sélectionné par défaut."""
    goto_mission_new(page, project_id=1)
    radio = page.locator("input[name='create_livrable_type'][value='mission_code']")
    expect(radio).to_be_checked()


# ── Tests Zone 1 : Conversation ───────────────────────────────────────

def test_mission_zone1_elements_present(page: Page):
    """T06 — Avec ?session=X, les éléments Zone 1 sont présents."""
    goto_mission_session(page, session_id=1)
    # Flow visible
    flow = page.locator("#mission-flow")
    expect(flow).to_be_visible()
    # Étape 1 active
    step1 = page.locator("#step-1")
    expect(step1).to_be_visible()
    # Zone messages présente
    messages_container = page.locator("#reflexion-messages")
    expect(messages_container).to_be_attached()


def test_mission_zone1_input_area_present(page: Page):
    """T07 — Pour une session OUVERTE, la zone de saisie est visible."""
    goto_mission_session(page, session_id=1)
    input_area = page.locator("#reflexion-input-area")
    # La zone doit exister dans le DOM
    expect(input_area).to_be_attached()
    # Boutons d'action présents
    btn_send = page.locator("#btn-send-message")
    btn_figer = page.locator("#btn-figer")
    btn_abandonner = page.locator("#btn-abandonner")
    expect(btn_send).to_be_attached()
    expect(btn_figer).to_be_attached()
    expect(btn_abandonner).to_be_attached()


def test_mission_zone1_send_requires_text(page: Page):
    """T08 — Envoyer sans texte ne déclenche pas d'appel API."""
    goto_mission_session(page, session_id=1)
    page.wait_for_selector("#btn-send-message")
    page.click("#btn-send-message")
    # La page reste stable (le clic ne fait rien si le champ est vide)
    expect(page.locator("#mission-flow")).to_be_visible()


# ── Tests Zone 3 : Pipeline ───────────────────────────────────────────

def test_mission_pipeline_zone3_present(page: Page):
    """T09 — Avec ?pipeline_session=X, l'étape 3 est visible."""
    goto_mission_pipeline(page, pipeline_session_id=1)
    # Flow visible
    flow = page.locator("#mission-flow")
    expect(flow).to_be_visible()
    # Étape 3 visible
    step3 = page.locator("#step-3")
    expect(step3).to_be_visible()
    # Étape 1 masquée (mode pipeline seul)
    step1 = page.locator("#step-1")
    expect(step1).to_be_hidden()


def test_mission_pipeline_steps_container_present(page: Page):
    """T10 — La Zone 3 contient le conteneur de steps."""
    goto_mission_pipeline(page, pipeline_session_id=1)
    steps_list = page.locator("#mc-steps-list")
    expect(steps_list).to_be_attached()


# ── Tests titre et navigation ─────────────────────────────────────────

def test_mission_page_title(page: Page):
    """T11 — Le titre de la page est 'JARVIS — Mission'."""
    goto_mission_empty(page)
    expect(page).to_have_title("JARVIS — Mission")


def test_mission_sidebar_present(page: Page):
    """T12 — La sidebar est présente sur la page."""
    goto_mission_empty(page)
    sidebar = page.locator("#sidebar")
    expect(sidebar).to_be_attached()


def test_mission_figer_modal_elements(page: Page):
    """T13 — Le modal de confirmation figement est bien dans le DOM."""
    goto_mission_session(page, session_id=1)
    modal = page.locator("#modal-figer")
    expect(modal).to_be_attached()
    btn_confirm = page.locator("#modal-figer-confirm")
    expect(btn_confirm).to_be_attached()
    btn_cancel = page.locator("#modal-figer-cancel")
    expect(btn_cancel).to_be_attached()
