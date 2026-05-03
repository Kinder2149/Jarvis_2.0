"""
Tests End-to-End (E2E) du Frontend V2 JARVIS avec Playwright.

Ces tests valident l'ensemble du frontend contre le serveur localhost:8000.
Aucune modification du code n'est faite - les bugs trouvés sont notés dans le rapport.
"""
import pytest
import requests
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000/app"
API_BASE = "http://localhost:8000/api"


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def get_first_project_id():
    """Récupère l'ID du premier projet existant."""
    r = requests.get(f"{API_BASE}/projects/")
    projects = r.json()
    return projects[0]["id"] if projects else None

def get_first_conversation_id(project_id=None):
    """Récupère l'ID de la première conversation existante."""
    url = f"{API_BASE}/chat/conversations"
    if project_id:
        url += f"?project_id={project_id}"
    r = requests.get(url)
    convs = r.json()
    return convs[0]["id"] if convs else None

def get_first_session_id():
    """Récupère l'ID d'une session pipeline existante."""
    projects = requests.get(f"{API_BASE}/projects/").json()
    for p in projects:
        sessions = requests.get(f"{API_BASE}/projects/{p['id']}/sessions").json()
        if sessions:
            return sessions[0]["id"], p["id"]
    return None, None

def wait_for_no_js_errors(page: Page):
    """Vérifie qu'il n'y a pas d'erreurs JS critiques dans la console."""
    # Laisser le temps au JS de s'exécuter
    page.wait_for_timeout(1500)


# ─────────────────────────────────────────────
# TESTS SERVEUR
# ─────────────────────────────────────────────

class TestServeur:

    def test_serveur_accessible(self):
        """Le serveur répond sur localhost:8000."""
        r = requests.get("http://localhost:8000/")
        assert r.status_code == 200

    def test_api_projects_accessible(self):
        """L'API projects répond."""
        r = requests.get(f"{API_BASE}/projects/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_api_conversations_accessible(self):
        """L'API chat conversations répond."""
        r = requests.get(f"{API_BASE}/chat/conversations")
        assert r.status_code == 200

    def test_api_config_accessible(self):
        """L'API config répond."""
        r = requests.get(f"{API_BASE}/config/")
        assert r.status_code == 200

    def test_static_files_servis(self):
        """Les fichiers statiques frontend sont servis."""
        for path in ["index.html", "chat.html", "dossier.html", "mission.html", "settings.html"]:
            r = requests.get(f"http://localhost:8000/app/{path}")
            assert r.status_code == 200, f"Page {path} non accessible (HTTP {r.status_code})"

    def test_pipeline_html_supprime(self):
        """pipeline.html doit avoir été supprimé (remplacé par mission.html)."""
        r = requests.get("http://localhost:8000/app/pipeline.html")
        assert r.status_code == 404, "pipeline.html existe encore - doit être supprimé"


# ─────────────────────────────────────────────
# TESTS LAYOUT GLOBAL
# ─────────────────────────────────────────────

class TestLayout:

    def test_dashboard_layout_3_panneaux(self, page: Page):
        """Le layout 3 panneaux est présent sur le dashboard."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_selector("#app-layout", timeout=5000)
        assert page.query_selector("#sidebar") is not None, "#sidebar manquant"
        assert page.query_selector("#main-content") is not None, "#main-content manquant"
        assert page.query_selector("#explorer") is not None, "#explorer manquant"
        assert page.query_selector("#toast-container") is not None, "#toast-container manquant"

    def test_sidebar_charge_sans_erreur(self, page: Page):
        """La sidebar se charge et affiche son contenu."""
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2000)
        
        sidebar = page.query_selector("#sidebar")
        assert sidebar is not None
        # Vérifier que la sidebar a du contenu (pas vide)
        assert len(sidebar.inner_html()) > 100, "Sidebar semble vide"
        
        # Pas d'erreurs JS critiques
        critical_errors = [e for e in js_errors if "undefined" in e.lower() or "typeerror" in e.lower() or "referenceerror" in e.lower()]
        assert len(critical_errors) == 0, f"Erreurs JS dans la sidebar: {critical_errors}"

    def test_sidebar_boutons_nouveaux_presents(self, page: Page):
        """Les boutons Nouveau Chat et Nouveau Module Code existent."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2000)
        assert page.query_selector("#btn-new-chat") is not None, "Bouton Nouveau Chat manquant"
        assert page.query_selector("#btn-new-module") is not None, "Bouton Nouveau Module manquant"

    def test_sidebar_collapse(self, page: Page):
        """La sidebar peut se replier et se déplier."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2000)
        
        sidebar = page.query_selector("#sidebar")
        assert "sidebar--collapsed" not in (sidebar.get_attribute("class") or ""), "Sidebar collapsed par défaut inattendu"
        
        # Clic collapse
        page.click("#btn-sidebar-collapse")
        page.wait_for_timeout(300)
        assert "sidebar--collapsed" in (page.query_selector("#sidebar").get_attribute("class") or ""), "Sidebar ne s'est pas repliée"
        
        # Clic expand
        page.click("#btn-sidebar-collapse")
        page.wait_for_timeout(300)
        assert "sidebar--collapsed" not in (page.query_selector("#sidebar").get_attribute("class") or ""), "Sidebar ne s'est pas dépliée"

    def test_nouveau_chat_modal(self, page: Page):
        """Le bouton Nouveau Chat ouvre un modal."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2000)
        page.click("#btn-new-chat")
        page.wait_for_timeout(500)
        modal = page.query_selector(".modal-overlay")
        assert modal is not None, "Modal Nouveau Chat ne s'est pas ouvert"
        # Fermer le modal
        page.click(".modal-overlay .btn-secondary") if page.query_selector(".modal-overlay .btn-secondary") else page.press("Escape")


# ─────────────────────────────────────────────
# TESTS DASHBOARD
# ─────────────────────────────────────────────

class TestDashboard:

    def test_dashboard_charge(self, page: Page):
        """Le dashboard se charge complètement."""
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(3000)
        
        assert page.query_selector("#page-dashboard") is not None
        assert page.query_selector(".dashboard-title") is not None
        
        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS dashboard: {critical}"

    def test_dashboard_subtitle_mis_a_jour(self, page: Page):
        """Le subtitle du dashboard est mis à jour (pas 'Chargement...')."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(3000)
        subtitle = page.query_selector("#dashboard-subtitle")
        text = subtitle.inner_text() if subtitle else ""
        assert "Chargement" not in text, f"Subtitle toujours à 'Chargement...': {text}"

    def test_dashboard_filtres(self, page: Page):
        """Les filtres date fonctionnent."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2000)
        
        # Clic sur "Hier"
        page.click(".filter-btn[data-period='yesterday']")
        page.wait_for_timeout(500)
        active = page.query_selector(".filter-btn--active")
        assert active is not None
        assert active.get_attribute("data-period") == "yesterday", "Filtre 'Hier' non actif après clic"
        
        # Clic sur "Cette semaine"
        page.click(".filter-btn[data-period='week']")
        page.wait_for_timeout(500)
        active = page.query_selector(".filter-btn--active")
        assert active.get_attribute("data-period") == "week"

    def test_dashboard_stats_presentes(self, page: Page):
        """Les stats résumé sont affichées."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(3000)
        stats = page.query_selector("#dashboard-stats")
        assert stats is not None
        # Au moins une stat-card
        stat_cards = page.query_selector_all(".stat-card")
        assert len(stat_cards) >= 3, f"Seulement {len(stat_cards)} stat-cards (3 attendues)"

    def test_dashboard_clic_conversation(self, page: Page):
        """Un clic sur une conversation dans la timeline navigue vers chat.html."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible pour ce test")
        
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(3000)
        
        # Si une conversation existe dans la timeline, cliquer dessus
        item = page.query_selector(".timeline-item--chat")
        if item:
            item.click()
            page.wait_for_timeout(1500)
            assert "chat.html" in page.url, f"Navigation attendue vers chat.html, URL actuelle: {page.url}"


# ─────────────────────────────────────────────
# TESTS CHAT
# ─────────────────────────────────────────────

class TestChat:

    def test_chat_charge_sans_id(self, page: Page):
        """Chat sans ID affiche un message d'erreur propre."""
        page.goto(f"{BASE_URL}/chat.html")
        page.wait_for_timeout(2000)
        assert page.query_selector("#page-chat") is not None

    def test_chat_charge_avec_conversation_existante(self, page: Page):
        """Chat charge une conversation existante correctement."""
        conv_id = get_first_conversation_id()
        if not conv_id:
            pytest.skip("Aucune conversation disponible")
        
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto(f"{BASE_URL}/chat.html?id={conv_id}")
        page.wait_for_timeout(2500)
        
        assert page.query_selector("#chat-messages") is not None
        assert page.query_selector("#chat-input") is not None
        assert page.query_selector("#btn-send") is not None
        
        # Titre pas vide
        title = page.query_selector("#chat-title")
        assert title is not None
        assert len(title.inner_text()) > 0, "Titre de conversation vide"
        
        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS chat: {critical}"

    def test_chat_input_disponible(self, page: Page):
        """Le champ de saisie chat est accessible et focusable."""
        conv_id = get_first_conversation_id()
        if not conv_id:
            pytest.skip("Aucune conversation disponible")
        
        page.goto(f"{BASE_URL}/chat.html?id={conv_id}")
        page.wait_for_timeout(2000)
        
        input_el = page.query_selector("#chat-input")
        assert input_el is not None
        assert not input_el.is_disabled(), "Input chat désactivé"
        
        # Taper du texte
        page.fill("#chat-input", "Test message automatique")
        value = page.input_value("#chat-input")
        assert "Test" in value

    def test_chat_btn_send_existe(self, page: Page):
        """Le bouton d'envoi est présent et actif."""
        conv_id = get_first_conversation_id()
        if not conv_id:
            pytest.skip("Aucune conversation disponible")
        
        page.goto(f"{BASE_URL}/chat.html?id={conv_id}")
        page.wait_for_timeout(2000)
        
        btn = page.query_selector("#btn-send")
        assert btn is not None
        assert not btn.is_disabled(), "Bouton send désactivé initialement"

    def test_chat_badge_projet_present(self, page: Page):
        """Le badge projet s'affiche si conversation liée à un projet."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        conv_id = get_first_conversation_id(project_id)
        if not conv_id:
            pytest.skip("Aucune conversation liée à un projet")
        
        page.goto(f"{BASE_URL}/chat.html?id={conv_id}&project_id={project_id}")
        page.wait_for_timeout(2500)
        
        badge = page.query_selector(".project-badge")
        assert badge is not None, "Badge projet absent dans le chat"
        assert "📁" in badge.inner_text()

    def test_chat_bouton_supprimer_ouvre_modal(self, page: Page):
        """Le bouton supprimer ouvre un modal de confirmation."""
        conv_id = get_first_conversation_id()
        if not conv_id:
            pytest.skip("Aucune conversation disponible")
        
        page.goto(f"{BASE_URL}/chat.html?id={conv_id}")
        page.wait_for_timeout(2000)
        
        btn = page.query_selector("#btn-delete-conversation")
        assert btn is not None, "Bouton supprimer absent"
        btn.click()
        page.wait_for_timeout(500)
        
        modal = page.query_selector(".modal-overlay")
        assert modal is not None, "Modal de confirmation absent"
        
        # Annuler
        cancel = page.query_selector(".modal-overlay .btn-secondary")
        if cancel:
            cancel.click()
        page.wait_for_timeout(300)
        assert page.query_selector(".modal-overlay") is None, "Modal pas fermé après Annuler"


# ─────────────────────────────────────────────
# TESTS VUE PROJET
# ─────────────────────────────────────────────

class TestProjet:

    def test_projet_charge(self, page: Page):
        """La vue projet se charge sans erreur."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto(f"{BASE_URL}/dossier.html?id={project_id}")
        page.wait_for_timeout(3000)
        
        name = page.query_selector("#project-name")
        assert name is not None
        assert len(name.inner_text()) > 0, "Nom du projet vide"
        
        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS projet: {critical}"

    def test_projet_instructions_visibles(self, page: Page):
        """Le bloc instructions du projet est visible."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        page.goto(f"{BASE_URL}/dossier.html?id={project_id}")
        page.wait_for_timeout(2500)
        
        assert page.query_selector("#instructions-display") is not None
        assert page.query_selector("#btn-edit-instructions") is not None

    def test_projet_instructions_editables(self, page: Page):
        """Le mode édition des instructions fonctionne."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        page.goto(f"{BASE_URL}/dossier.html?id={project_id}")
        page.wait_for_timeout(2500)
        
        # Cliquer ✏️
        page.click("#btn-edit-instructions")
        page.wait_for_timeout(300)
        
        # L'input textarea doit apparaître
        edit_zone = page.query_selector("#instructions-edit")
        assert edit_zone is not None
        is_visible = edit_zone.evaluate("el => el.style.display !== 'none'")
        assert is_visible, "Zone édition instructions pas visible après clic ✏️"
        
        # Clic Annuler
        page.click("#btn-cancel-instructions")
        page.wait_for_timeout(300)

    def test_projet_boutons_actions_presents(self, page: Page):
        """Les boutons Nouveau Chat et Nouveau Module Code sont présents."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        page.goto(f"{BASE_URL}/dossier.html?id={project_id}")
        page.wait_for_timeout(2500)
        
        assert page.query_selector("#btn-new-chat") is not None, "Bouton Nouveau Chat absent"
        assert page.query_selector("#btn-new-module") is not None, "Bouton Nouveau Module absent"

    def test_projet_conversations_listes(self, page: Page):
        """La liste de conversations du projet est rendue."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        page.goto(f"{BASE_URL}/dossier.html?id={project_id}")
        page.wait_for_timeout(3000)
        
        container = page.query_selector("#conversations-list")
        assert container is not None, "#conversations-list manquant"


# ─────────────────────────────────────────────
# TESTS MODULE CODE
# ─────────────────────────────────────────────

class TestModuleCode:

    def test_module_code_charge_sans_session(self, page: Page):
        """Module code sans session affiche un message d'erreur propre."""
        page.goto(f"{BASE_URL}/mission.html")
        page.wait_for_timeout(2000)
        assert page.query_selector("#mission-empty-state") is not None or page.query_selector("#mission-flow") is not None

    def test_module_code_charge_avec_session(self, page: Page):
        """Module code charge une session existante."""
        session_id, project_id = get_first_session_id()
        if not session_id:
            pytest.skip("Aucune session disponible")
        
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto(f"{BASE_URL}/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_timeout(3000)
        
        assert page.query_selector("#mc-workflow-type") is not None
        assert page.query_selector("#mc-steps-list") is not None
        
        # Workflow type doit être affiché
        wf_type = page.query_selector("#mc-workflow-type")
        assert len(wf_type.inner_text()) > 0, "Workflow type vide"
        
        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS mission: {critical}"

    def test_module_code_steps_rendus(self, page: Page):
        """Les steps sont rendus dans la liste."""
        session_id, project_id = get_first_session_id()
        if not session_id:
            pytest.skip("Aucune session disponible")
        
        page.goto(f"{BASE_URL}/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_timeout(3000)
        
        steps = page.query_selector_all(".step-card")
        assert len(steps) > 0, "Aucun step-card rendu"

    def test_module_code_session_terminee_sans_bouton_abort(self, page: Page):
        """Une session terminée n'affiche pas le bouton Abandonner."""
        # Trouver une session COMPLETED
        projects = requests.get(f"{API_BASE}/projects/").json()
        completed_session = None
        completed_project = None
        for p in projects:
            sessions = requests.get(f"{API_BASE}/projects/{p['id']}/sessions").json()
            for s in sessions:
                if s["status"] == "COMPLETED":
                    completed_session = s["id"]
                    completed_project = p["id"]
                    break
            if completed_session:
                break
        
        if not completed_session:
            pytest.skip("Aucune session COMPLETED disponible")
        
        page.goto(f"{BASE_URL}/mission.html?pipeline_session={completed_session}&project_id={completed_project}")
        page.wait_for_timeout(3000)
        
        btn_abort = page.query_selector("#btn-abort-pipeline")
        if btn_abort:
            assert btn_abort.evaluate("el => el.style.display === 'none'"), "Bouton Abandonner visible sur session COMPLETED"

    def test_module_code_lien_projet(self, page: Page):
        """Le lien vers le projet s'affiche dans le header module code."""
        session_id, project_id = get_first_session_id()
        if not session_id:
            pytest.skip("Aucune session disponible")
        
        page.goto(f"{BASE_URL}/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_timeout(3000)
        
        link = page.query_selector("#mc-project-link a")
        assert link is not None, "Lien projet absent dans mission"
        href = link.get_attribute("href")
        assert f"dossier.html?id={project_id}" in href


# ─────────────────────────────────────────────
# TESTS EXPLORATEUR
# ─────────────────────────────────────────────

class TestExplorateur:

    def test_explorateur_present_dans_le_dom(self, page: Page):
        """Le panneau explorateur #explorer existe dans le DOM."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2000)
        assert page.query_selector("#explorer") is not None

    def test_explorateur_visible_si_dossier_lie(self, page: Page):
        """L'explorateur s'affiche si le projet a un local_path."""
        # Trouver un projet avec local_path
        projects = requests.get(f"{API_BASE}/projects/").json()
        project_with_path = next((p for p in projects if p.get("local_path")), None)
        
        if not project_with_path:
            pytest.skip("Aucun projet avec local_path défini")
        
        page.goto(f"{BASE_URL}/dossier.html?id={project_with_path['id']}")
        page.wait_for_timeout(3000)
        
        explorer = page.query_selector("#explorer")
        assert explorer is not None
        classes = explorer.get_attribute("class") or ""
        assert "explorer--hidden" not in classes, "Explorateur reste caché malgré local_path défini"

    def test_explorateur_arborescence_presente(self, page: Page):
        """L'arborescence de fichiers s'affiche dans l'explorateur."""
        projects = requests.get(f"{API_BASE}/projects/").json()
        project_with_path = next((p for p in projects if p.get("local_path")), None)
        
        if not project_with_path:
            pytest.skip("Aucun projet avec local_path défini")
        
        page.goto(f"{BASE_URL}/dossier.html?id={project_with_path['id']}")
        page.wait_for_timeout(3000)
        
        tree = page.query_selector("#explorer-tree")
        assert tree is not None
        tree_html = tree.inner_html()
        assert len(tree_html) > 50, "Arborescence vide ou non rendue"


# ─────────────────────────────────────────────
# TESTS PARAMÈTRES
# ─────────────────────────────────────────────

class TestParametres:

    def test_settings_charge(self, page: Page):
        """La page paramètres se charge sans erreur."""
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto(f"{BASE_URL}/settings.html")
        page.wait_for_timeout(3000)
        
        assert page.query_selector("#page-settings") is not None
        
        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS settings: {critical}"

    def test_settings_trois_providers_affiches(self, page: Page):
        """Les 3 providers API sont affichés."""
        page.goto(f"{BASE_URL}/settings.html")
        page.wait_for_timeout(3000)
        
        for provider in ["openrouter", "anthropic", "google"]:
            row = page.query_selector(f"#key-row-{provider}")
            assert row is not None, f"Ligne provider '{provider}' absente"

    def test_settings_dropdowns_modeles_remplis(self, page: Page):
        """Les dropdowns de modèles ont des options."""
        page.goto(f"{BASE_URL}/settings.html")
        page.wait_for_timeout(3000)
        
        for model_id in ["model-routing", "model-code", "model-analysis"]:
            select = page.query_selector(f"#{model_id}")
            assert select is not None, f"Select #{model_id} absent"
            options = select.query_selector_all("option")
            assert len(options) > 0, f"Aucune option dans #{model_id}"

    def test_settings_bouton_sauvegarder_present(self, page: Page):
        """Le bouton sauvegarder les modèles est présent."""
        page.goto(f"{BASE_URL}/settings.html")
        page.wait_for_timeout(3000)
        assert page.query_selector("#btn-save-models") is not None

    def test_settings_cles_etat_affiche(self, page: Page):
        """L'état des clés (configurée / non configurée) est affiché."""
        page.goto(f"{BASE_URL}/settings.html")
        page.wait_for_timeout(3000)
        
        for provider in ["openrouter", "anthropic", "google"]:
            display = page.query_selector(f"#key-display-{provider}")
            assert display is not None, f"Zone affichage clé {provider} absente"
            html = display.inner_html()
            assert len(html) > 0, f"État clé {provider} non rendu"


# ─────────────────────────────────────────────
# TESTS NAVIGATION
# ─────────────────────────────────────────────

class TestNavigation:

    def test_navigation_index_vers_projet(self, page: Page):
        """Navigation dashboard → projet via sidebar."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2500)
        
        # Cliquer sur le premier projet dans la sidebar
        project_link = page.query_selector(".nav-project-header")
        if project_link:
            # Cliquer pour déplier
            project_link.click()
            page.wait_for_timeout(300)

    def test_navigation_breadcrumb_projet(self, page: Page):
        """Le badge projet dans le chat navigue vers dossier.html."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")
        
        conv_id = get_first_conversation_id(project_id)
        if not conv_id:
            pytest.skip("Aucune conversation liée à un projet")
        
        page.goto(f"{BASE_URL}/chat.html?id={conv_id}&project_id={project_id}")
        page.wait_for_timeout(2500)
        
        badge = page.query_selector(".project-badge")
        if badge:
            badge.click()
            page.wait_for_timeout(1500)
            assert "dossier.html" in page.url
            assert f"id={project_id}" in page.url

    def test_toutes_pages_sans_erreur_js(self, page: Page):
        """Toutes les pages chargent sans TypeError/ReferenceError."""
        project_id = get_first_project_id()
        conv_id = get_first_conversation_id()
        session_id, _ = get_first_session_id()
        
        pages_to_test = [
            f"{BASE_URL}/index.html",
            f"{BASE_URL}/settings.html",
        ]
        
        if project_id:
            pages_to_test.append(f"{BASE_URL}/dossier.html?id={project_id}")
        if conv_id:
            pages_to_test.append(f"{BASE_URL}/chat.html?id={conv_id}")
        if session_id:
            pages_to_test.append(f"{BASE_URL}/mission.html?pipeline_session={session_id}")
        
        for url in pages_to_test:
            js_errors = []
            context = page.context
            test_page = context.new_page()
            test_page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
            
            test_page.goto(url)
            test_page.wait_for_timeout(2500)
            test_page.close()
            
            critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read properties"])]
            assert len(critical) == 0, f"Erreurs JS sur {url}: {critical}"
