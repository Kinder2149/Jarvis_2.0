import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def base_url():
    return "http://localhost:8000"


def test_sidebar_contains_reflexion_button(page: Page, base_url):
    """Vérifie que le bouton Nouvelle Réflexion est visible dans la sidebar."""
    page.goto(f"{base_url}/app/index.html")
    
    sidebar = page.locator("#sidebar")
    expect(sidebar).to_be_visible()
    
    reflexion_button = page.locator("#btn-new-reflexion")
    expect(reflexion_button).to_be_visible()
    expect(reflexion_button).to_contain_text("Nouvelle Réflexion")


def test_page_reflexion_loads(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    expect(page.locator("#reflexion-empty-state")).to_be_visible()
    expect(page.locator("h2")).to_contain_text("Module Réflexion")


def test_create_reflexion_modal(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    page.click("#btn-new-reflexion-empty")
    
    expect(page.locator("#modal-new-reflexion")).to_be_visible()
    expect(page.locator("#modal-new-reflexion h2")).to_contain_text("Nouvelle réflexion")
    
    expect(page.locator("#new-reflexion-project")).to_be_visible()
    expect(page.locator('input[name="livrable_type"][value="mission_code"]')).to_be_checked()
    
    page.click("#modal-new-reflexion-close")
    expect(page.locator("#modal-new-reflexion")).not_to_be_visible()


def test_create_reflexion_and_redirect(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    page.click("#btn-new-reflexion-empty")
    
    page.select_option("#new-reflexion-project", index=0)
    page.check('input[name="livrable_type"][value="decision_figee"]')
    
    page.click("#modal-new-reflexion-create")
    
    page.wait_for_url("**/reflexion.html?session=*", timeout=5000)
    
    expect(page.locator("#reflexion-content")).to_be_visible()
    expect(page.locator("#reflexion-livrable")).to_contain_text("Décision figée")


def test_session_view_ouverte(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    page.click("#btn-new-reflexion-empty")
    page.select_option("#new-reflexion-project", index=0)
    page.click("#modal-new-reflexion-create")
    
    page.wait_for_url("**/reflexion.html?session=*", timeout=5000)
    
    expect(page.locator("#reflexion-status-badge")).to_contain_text("Ouverte")
    
    expect(page.locator("#reflexion-input")).to_be_enabled()
    expect(page.locator("#btn-send-message")).to_be_enabled()
    expect(page.locator("#btn-figer")).to_be_enabled()
    expect(page.locator("#btn-abandonner")).to_be_enabled()


def test_cadrage_health_panel(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    page.click("#btn-new-reflexion-empty")
    page.select_option("#new-reflexion-project", index=0)
    page.click("#modal-new-reflexion-create")
    
    page.wait_for_url("**/reflexion.html?session=*", timeout=5000)
    
    page.wait_for_selector("#cadrage-health-panel", state="visible", timeout=10000)
    
    expect(page.locator("#cadrage-verdict")).to_be_visible()
    
    verdict_text = page.locator("#cadrage-verdict").inner_text()
    assert any(icon in verdict_text for icon in ['🟢', '🟠', '🔴'])


def test_toggle_cadrage_details(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    page.click("#btn-new-reflexion-empty")
    page.select_option("#new-reflexion-project", index=0)
    page.click("#modal-new-reflexion-create")
    
    page.wait_for_url("**/reflexion.html?session=*", timeout=5000)
    page.wait_for_selector("#cadrage-health-panel", state="visible", timeout=10000)
    
    expect(page.locator("#cadrage-details")).not_to_be_visible()
    
    page.click("#btn-toggle-cadrage")
    expect(page.locator("#cadrage-details")).to_be_visible()
    
    page.click("#btn-toggle-cadrage")
    expect(page.locator("#cadrage-details")).not_to_be_visible()


def test_figer_button_modal(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    page.click("#btn-new-reflexion-empty")
    page.select_option("#new-reflexion-project", index=0)
    page.click("#modal-new-reflexion-create")
    
    page.wait_for_url("**/reflexion.html?session=*", timeout=5000)
    
    page.click("#btn-figer")
    
    expect(page.locator("#modal-figer")).to_be_visible()
    expect(page.locator("#modal-figer h2")).to_contain_text("Figer cette réflexion")
    expect(page.locator("#modal-figer .modal-body")).to_contain_text("irréversible")
    
    page.click("#modal-figer-cancel")
    expect(page.locator("#modal-figer")).not_to_be_visible()


def test_abandon_session_confirmation(page: Page, base_url):
    page.goto(f"{base_url}/app/reflexion.html")
    
    page.click("#btn-new-reflexion-empty")
    page.select_option("#new-reflexion-project", index=0)
    page.click("#modal-new-reflexion-create")
    
    page.wait_for_url("**/reflexion.html?session=*", timeout=5000)
    
    page.on("dialog", lambda dialog: dialog.dismiss())
    page.click("#btn-abandonner")
    
    expect(page.locator("#reflexion-status-badge")).to_contain_text("Ouverte")
