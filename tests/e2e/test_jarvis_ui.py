"""
Tests E2E UI JARVIS — Avec navigateur Playwright + LLM réel.
Scénarios 1-3 : conversation basique, routing ATELIER, abandon flow.

⚠️ Ces tests nécessitent :
- Serveur JARVIS actif sur localhost:8000
- Clés API configurées (OpenRouter ou Anthropic)
- Timeout adapté aux appels LLM (30s)
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e_ui
def test_scenario_1_jarvis_basic_conversation(page: Page, base_url: str):
    """
    SCÉNARIO 1 — Conversation JARVIS basique.
    
    1. Ouvrir /app/jarvis.html
    2. Vérifier 6 cartes agents visibles
    3. Envoyer "Bonjour"
    4. Attendre réponse (max 30s)
    5. Vérifier badge agent = "JARVIS"
    6. Vérifier contenu réponse non vide
    """
    # 1. Ouvrir jarvis.html
    page.goto(f"{base_url}/app/jarvis.html")
    page.wait_for_load_state("networkidle")
    
    # 2. Vérifier que les 6 cartes agents sont visibles
    # JARVIS (featured card)
    expect(page.locator("#jcard-JARVIS")).to_be_visible()
    
    # 5 autres agents dans la grille
    expect(page.locator("#jcard-MENTOR")).to_be_visible()
    expect(page.locator("#jcard-FORGE")).to_be_visible()
    expect(page.locator("#jcard-SENTINELLE")).to_be_visible()
    expect(page.locator("#jcard-ATELIER")).to_be_visible()
    expect(page.locator("#jcard-MEDIA")).to_be_visible()
    
    # 3. Envoyer le message "Bonjour"
    input_field = page.locator("#jchat-input")
    expect(input_field).to_be_visible()
    input_field.fill("Bonjour")
    
    send_button = page.locator("#jchat-send")
    send_button.click()
    
    # 4. Attendre la réponse (max 30s)
    # La réponse assistant apparaît dans un .jmsg avec data-role="assistant"
    assistant_message = page.locator('.jmsg[data-role="assistant"]').last
    expect(assistant_message).to_be_visible(timeout=30000)
    
    # 5. Vérifier badge agent = "JARVIS"
    agent_badge = assistant_message.locator(".jmsg-agent-badge")
    expect(agent_badge).to_contain_text("JARVIS", timeout=5000)
    
    # 6. Vérifier contenu réponse non vide
    message_content = assistant_message.locator(".jmsg-content")
    content_text = message_content.inner_text()
    assert len(content_text) > 0, "Response content is empty"
    assert len(content_text) > 10, f"Response too short: {content_text}"


@pytest.mark.e2e_ui
def test_scenario_2_routing_atelier(page: Page, base_url: str):
    """
    SCÉNARIO 2 — Routing ATELIER.
    
    1. Ouvrir /app/jarvis.html (nouvelle conversation)
    2. Envoyer "Je veux créer un nouveau prospect"
    3. Attendre réponse (max 30s)
    4. Vérifier badge agent = "ATELIER"
    5. Vérifier réponse contient "nom" ou "restaurant"
    """
    # 1. Ouvrir jarvis.html (nouvelle conversation créée automatiquement)
    page.goto(f"{base_url}/app/jarvis.html")
    page.wait_for_load_state("networkidle")
    
    # Attendre que l'interface soit prête
    expect(page.locator("#jchat-input")).to_be_visible()
    
    # 2. Envoyer le message
    input_field = page.locator("#jchat-input")
    input_field.fill("Je veux créer un nouveau prospect")
    
    send_button = page.locator("#jchat-send")
    send_button.click()
    
    # 3. Attendre la réponse (max 30s)
    assistant_message = page.locator('.jmsg[data-role="assistant"]').last
    expect(assistant_message).to_be_visible(timeout=30000)
    
    # 4. Vérifier badge agent = "ATELIER"
    agent_badge = assistant_message.locator(".jmsg-agent-badge")
    expect(agent_badge).to_contain_text("ATELIER", timeout=5000)
    
    # 5. Vérifier que la réponse contient "nom" ou "restaurant"
    message_content = assistant_message.locator(".jmsg-content")
    content_text = message_content.inner_text().lower()
    
    assert "nom" in content_text or "restaurant" in content_text or "établissement" in content_text, \
        f"Expected ATELIER to ask for name/restaurant, got: {content_text[:200]}"


@pytest.mark.e2e_ui
def test_scenario_3_abandon_atelier_flow(page: Page, base_url: str):
    """
    SCÉNARIO 3 — Abandon flow ATELIER (bug corrigé).
    
    1. Ouvrir /app/jarvis.html
    2. Envoyer "Je veux créer un nouveau prospect"
    3. Attendre réponse ATELIER
    4. Envoyer "non erreur je veux faire un audit du projet paperclip"
    5. Attendre réponse (max 30s)
    6. Vérifier que la réponse NE contient PAS "URL" ni "site web"
    7. Vérifier que l'agent est "JARVIS" ou "MENTOR" (pas "ATELIER")
    """
    # 1. Ouvrir jarvis.html
    page.goto(f"{base_url}/app/jarvis.html")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#jchat-input")).to_be_visible()
    
    # 2. Envoyer "Je veux créer un nouveau prospect"
    input_field = page.locator("#jchat-input")
    input_field.fill("Je veux créer un nouveau prospect")
    page.locator("#jchat-send").click()
    
    # 3. Attendre réponse ATELIER
    first_response = page.locator('.jmsg[data-role="assistant"]').first
    expect(first_response).to_be_visible(timeout=30000)
    
    # Vérifier que c'est bien ATELIER qui a répondu
    first_badge = first_response.locator(".jmsg-agent-badge")
    expect(first_badge).to_contain_text("ATELIER", timeout=5000)
    
    # 4. Envoyer message d'abandon
    input_field.fill("non erreur je veux faire un audit du projet paperclip")
    page.locator("#jchat-send").click()
    
    # 5. Attendre la deuxième réponse (max 30s)
    # Attendre qu'il y ait au moins 2 messages assistant
    page.wait_for_selector('.jmsg[data-role="assistant"]', timeout=30000)
    
    # Récupérer le dernier message assistant (la 2ème réponse)
    all_assistant_messages = page.locator('.jmsg[data-role="assistant"]').all()
    assert len(all_assistant_messages) >= 2, "Expected at least 2 assistant messages"
    
    second_response = all_assistant_messages[-1]
    
    # 6. Vérifier que la réponse NE contient PAS "URL" ni "site web"
    content = second_response.locator(".jmsg-content")
    content_text = content.inner_text().lower()
    
    assert "url" not in content_text, f"ATELIER should have aborted, but still asking for URL: {content_text[:200]}"
    assert "site web" not in content_text, f"ATELIER should have aborted, but still asking for site: {content_text[:200]}"
    
    # 7. Vérifier que l'agent est "JARVIS" ou "MENTOR" (pas "ATELIER")
    second_badge = second_response.locator(".jmsg-agent-badge")
    badge_text = second_badge.inner_text()
    
    assert badge_text in ["JARVIS", "MENTOR"], \
        f"Expected JARVIS or MENTOR after abort, got: {badge_text}"


@pytest.mark.e2e_ui
def test_ui_agents_cards_clickable(page: Page, base_url: str):
    """
    Test bonus : vérifier que les cartes agents sont cliquables.
    """
    page.goto(f"{base_url}/app/jarvis.html")
    page.wait_for_load_state("networkidle")
    
    # Cliquer sur la carte MENTOR
    mentor_card = page.locator("#jcard-MENTOR")
    expect(mentor_card).to_be_visible()
    mentor_card.click()
    
    # Vérifier que la carte devient active (classe jagent-card--active)
    expect(mentor_card).to_have_class("jagent-card jagent-card--active")
    
    # Vérifier que JARVIS n'est plus active
    jarvis_card = page.locator("#jcard-JARVIS")
    expect(jarvis_card).not_to_have_class("jagent-card jagent-card--active")
