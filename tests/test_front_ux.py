"""
Tests E2E — UX Refactoring Frontend (FRONT-01 à FRONT-06)

Valide les 6 missions de correction UX livrées le 2026-04-18.
Prérequis : serveur JARVIS actif sur http://localhost:8000

Certains tests sont conditionnels (pytest.skip si données absentes).
"""
import pytest
import requests
from playwright.sync_api import Page

BASE_URL = "http://localhost:8000/app"
API_BASE = "http://localhost:8000/api"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_first_project_id():
    r = requests.get(f"{API_BASE}/projects/")
    projects = r.json()
    return projects[0]["id"] if projects else None


def get_session_by_status(status):
    """Cherche une session avec le statut donné dans tous les projets."""
    projects = requests.get(f"{API_BASE}/projects/").json()
    for p in projects:
        sessions = requests.get(f"{API_BASE}/projects/{p['id']}/sessions").json()
        for s in sessions:
            if s["status"] == status:
                return s["id"], p["id"]
    return None, None


def get_waiting_validation_session_with_human_step():
    """Cherche une session WAITING_VALIDATION avec un step requires_validation=1."""
    projects = requests.get(f"{API_BASE}/projects/").json()
    for p in projects:
        sessions = requests.get(f"{API_BASE}/projects/{p['id']}/sessions").json()
        for s in sessions:
            if s["status"] == "WAITING_VALIDATION":
                # Vérifier les steps
                session_detail = requests.get(f"{API_BASE}/pipelines/{s['id']}").json()
                steps = session_detail.get("steps", [])
                has_human_step = any(
                    st.get("status") == "WAITING_VALIDATION" and st.get("requires_validation") == 1
                    for st in steps
                )
                if has_human_step:
                    return s["id"], p["id"]
    return None, None


# ─── FRONT-01 : CTA post-session Module Code ──────────────────────────────────

class TestFront01CTAModuleCode:
    """
    FRONT-01 : Quand une session est COMPLETED/ABORTED/ERROR, la page module-code
    ne doit plus être morte — elle affiche une zone d'action contextuelle.
    """

    def test_api_sessions_ont_champ_status(self):
        """Vérification API : GET /projects/{id}/sessions retourne 'status' par session."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")

        sessions = requests.get(f"{API_BASE}/projects/{project_id}/sessions").json()
        if not sessions:
            pytest.skip("Aucune session disponible pour ce projet")

        for s in sessions:
            assert "status" in s, f"Champ 'status' manquant dans la session {s.get('id')}"

    def test_cta_session_completed_visible(self, page: Page):
        """Session COMPLETED → zone CTA visible avec message succès (pas page morte)."""
        session_id, project_id = get_session_by_status("COMPLETED")
        if not session_id:
            pytest.skip("Aucune session COMPLETED disponible")

        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_timeout(3000)

        action_zone = page.query_selector("#mc-action-zone")
        assert action_zone is not None, "#mc-action-zone absent dans mission.html"

        is_visible = action_zone.evaluate("el => el.style.display !== 'none'")
        assert is_visible, "Zone CTA masquée pour une session COMPLETED (page morte)"

        zone_html = action_zone.inner_html()
        assert any(s in zone_html for s in ["✅", "terminée", "succès"]), \
            f"Message de succès absent dans la zone CTA : {zone_html[:300]}"

        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS : {critical}"

    def test_cta_session_aborted_visible(self, page: Page):
        """Session ABORTED → zone CTA visible avec message abandon (pas page morte)."""
        session_id, project_id = get_session_by_status("ABORTED")
        if not session_id:
            pytest.skip("Aucune session ABORTED disponible")

        page.goto(f"{BASE_URL}/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_timeout(3000)

        action_zone = page.query_selector("#mc-action-zone")
        assert action_zone is not None, "#mc-action-zone absent"

        is_visible = action_zone.evaluate("el => el.style.display !== 'none'")
        assert is_visible, "Zone CTA masquée pour une session ABORTED (page morte)"

        zone_html = action_zone.inner_html()
        assert any(s in zone_html for s in ["❌", "⛔", "abandonn", "échec"]), \
            f"Message ABORTED absent dans la zone CTA : {zone_html[:300]}"

    def test_cta_bouton_retour_projet_present(self, page: Page):
        """Session terminée → bouton/lien 'Retour au projet' présent dans la zone CTA."""
        session_id, project_id = get_session_by_status("COMPLETED")
        if not session_id:
            session_id, project_id = get_session_by_status("ABORTED")
        if not session_id:
            pytest.skip("Aucune session terminée disponible")

        page.goto(f"{BASE_URL}/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_timeout(3000)

        action_zone = page.query_selector("#mc-action-zone")
        if not action_zone:
            pytest.skip("Zone CTA absente")

        # Chercher un lien vers dossier.html dans la zone CTA (refactoring module_type)
        link = action_zone.query_selector("a[href*='dossier.html']")
        assert link is not None, "Lien 'Retour au projet' absent dans la zone CTA"

    def test_regression_waiting_validation_toujours_fonctionnel(self, page: Page):
        """RÉGRESSION FRONT-01 : session WAITING_VALIDATION → zone de validation toujours visible."""
        session_id, project_id = get_waiting_validation_session_with_human_step()
        if not session_id:
            pytest.skip("Aucune session WAITING_VALIDATION avec step humain disponible")

        page.goto(f"{BASE_URL}/mission.html?pipeline_session={session_id}&project_id={project_id}")
        page.wait_for_timeout(3000)

        action_zone = page.query_selector("#mc-action-zone")
        assert action_zone is not None

        is_visible = action_zone.evaluate("el => el.style.display !== 'none'")
        assert is_visible, "Zone validation masquée pour WAITING_VALIDATION (régression FRONT-01)"


# ─── FRONT-02 : CTA + retry Atelier ──────────────────────────────────────────

class TestFront02CTAAtelier:
    """
    FRONT-02 : La page atelier ne doit pas être morte après FAILED/ABORTED.
    Les steps en ERROR/FAILED doivent avoir un bouton retry.
    """

    def test_atelier_charge_sans_erreur_js(self, page: Page):
        """atelier.html charge sans TypeError/ReferenceError."""
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/atelier.html")
        page.wait_for_timeout(3000)

        assert page.query_selector("#view-prospects") is not None, "#view-prospects absent dans atelier.html"

        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS Atelier : {critical}"

    def test_cta_pipeline_aborted_visible(self, page: Page):
        """Pipeline Atelier ABORTED → zone CTA visible avec bouton retour kanban."""
        # Trouver un prospect avec pipeline ABORTED
        r = requests.get(f"{API_BASE}/atelier/prospects")
        prospects = r.json()
        aborted_prospect = next(
            (p for p in prospects if p.get("session_status") == "ABORTED"),
            None
        )
        if not aborted_prospect:
            pytest.skip("Aucun prospect avec pipeline ABORTED disponible")

        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/atelier.html?prospect_id={aborted_prospect['id']}")
        page.wait_for_timeout(3000)

        # Trouver la zone d'action
        # Elle peut être dans la vue pipeline du prospect
        content = page.content()
        assert any(s in content for s in ["Pipeline abandonné", "⛔", "abandonné"]), \
            "Message ABORTED absent dans la page atelier"

        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS : {critical}"

    def test_retry_step_visible_sur_step_error(self, page: Page):
        """Un step en ERROR/FAILED affiche un bouton retry 🔄."""
        # Chercher un prospect dont le pipeline a un step en ERROR ou FAILED
        r = requests.get(f"{API_BASE}/atelier/prospects")
        prospects = r.json()

        prospect_with_error = None
        for p in prospects:
            if p.get("session_id"):
                session = requests.get(f"{API_BASE}/pipelines/{p['session_id']}").json()
                error_steps = [s for s in session.get("steps", []) if s["status"] in ("ERROR", "FAILED")]
                if error_steps:
                    prospect_with_error = p
                    break

        if not prospect_with_error:
            pytest.skip("Aucun prospect avec step en ERROR/FAILED disponible")

        page.goto(f"{BASE_URL}/atelier.html?prospect_id={prospect_with_error['id']}")
        page.wait_for_timeout(3000)

        # Un bouton retry doit être visible sur la step card
        # Il utilise onclick="window.retryAtelierStep(...)"
        retry_buttons = page.query_selector_all("[onclick*='retryAtelierStep']")
        assert len(retry_buttons) > 0, "Bouton retry absent sur step en ERROR/FAILED (FRONT-02)"


# ─── FRONT-03 : Compteur sidebar Atelier ─────────────────────────────────────

class TestFront03SidebarCounter:
    """
    FRONT-03 : GET /atelier/prospects doit retourner session_status.
    Le badge sidebar doit compter les WAITING_VALIDATION, pas les en_analyse.
    """

    def test_prospects_retournent_session_status(self):
        """GET /atelier/prospects : chaque prospect a le champ session_status."""
        r = requests.get(f"{API_BASE}/atelier/prospects")
        assert r.status_code == 200, f"GET /atelier/prospects → {r.status_code}"

        prospects = r.json()
        if not prospects:
            pytest.skip("Aucun prospect disponible")

        for p in prospects:
            assert "session_status" in p, \
                f"Champ 'session_status' manquant dans le prospect id={p.get('id')}"

    def test_prospect_sans_session_a_status_null(self):
        """Prospect sans session → session_status doit être null."""
        r = requests.get(f"{API_BASE}/atelier/prospects")
        prospects = r.json()

        sans_session = [p for p in prospects if not p.get("session_id")]
        if not sans_session:
            pytest.skip("Tous les prospects ont une session")

        for p in sans_session:
            assert p.get("session_status") is None, \
                f"Prospect sans session devrait avoir session_status=null, " \
                f"got: {p.get('session_status')} (id={p.get('id')})"

    def test_prospect_avec_session_a_status_non_null(self):
        """Prospect avec session → session_status doit être non null."""
        r = requests.get(f"{API_BASE}/atelier/prospects")
        prospects = r.json()

        avec_session = [p for p in prospects if p.get("session_id")]
        if not avec_session:
            pytest.skip("Aucun prospect avec session disponible")

        for p in avec_session:
            assert p.get("session_status") is not None, \
                f"Prospect avec session devrait avoir session_status non-null " \
                f"(id={p.get('id')}, session_id={p.get('session_id')})"


# ─── FRONT-04 : Kanban badges visuels ────────────────────────────────────────

class TestFront04KanbanBadges:
    """
    FRONT-04 : Les cards kanban doivent afficher des icônes différenciées
    selon session_status (⏸️ WAITING_VALIDATION, ⚙️ RUNNING, ✅ COMPLETED, etc.)
    """

    def test_kanban_charge_sans_erreur(self, page: Page):
        """atelier.html kanban charge sans erreur JS."""
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/atelier.html")
        page.wait_for_timeout(3000)

        assert page.query_selector("#kanban-board") is not None, "#kanban-board absent"

        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS kanban : {critical}"

    def test_icones_statut_presentes_dans_kanban(self, page: Page):
        """Les cards kanban avec session affichent des icônes de statut différenciées."""
        r = requests.get(f"{API_BASE}/atelier/prospects")
        prospects_with_session = [p for p in r.json() if p.get("session_id")]

        if not prospects_with_session:
            pytest.skip("Aucun prospect avec session — impossible de tester les badges")

        page.goto(f"{BASE_URL}/atelier.html")
        page.wait_for_timeout(3000)

        kanban = page.query_selector("#kanban-board")
        assert kanban is not None

        # Skip si le kanban est vide (données manquantes — pas un bug de code)
        cards = page.query_selector_all(".kanban-card")
        if len(cards) == 0:
            pytest.skip("Kanban vide — aucun prospect affiché (kanban_status non correspondant)")

        kanban_html = kanban.inner_html()
        title_indicators = [
            'title="En attente de validation"',
            'title="Terminé"',
            'title="Erreur"',
            'title="Abandonné"',
            'title="IA en cours'
        ]
        has_any = any(t in kanban_html for t in title_indicators)
        assert has_any, (
            f"Aucun indicateur de statut session dans le kanban "
            f"(title manquant). HTML (300 chars) : {kanban_html[:300]}"
        )

    def test_animation_pulse_css_definie(self):
        """CSS : l'animation pulse-icon est définie dans style.css (FRONT-04)."""
        r = requests.get("http://localhost:8000/app/assets/style.css")
        assert r.status_code == 200
        css = r.text
        assert "pulse-icon" in css, "Animation CSS pulse-icon absente (FRONT-04 non appliqué)"


# ─── FRONT-05 : Dashboard "En attente de toi" ────────────────────────────────

class TestFront05DashboardWaiting:
    """
    FRONT-05 : Le dashboard doit distinguer WAITING_VALIDATION (urgent, en tête)
    de RUNNING (secondaire). Un banner orange s'affiche si des validations attendent.
    """

    def test_css_waiting_banner_defini(self):
        """CSS : .waiting-banner et .card--waiting sont définis (FRONT-05)."""
        r = requests.get("http://localhost:8000/app/assets/style.css")
        css = r.text
        assert ".waiting-banner" in css, "Classe CSS .waiting-banner absente (FRONT-05)"
        assert "card--waiting" in css, "Classe CSS .card--waiting absente (FRONT-05)"

    def test_section_sessions_actives_titre_mis_a_jour(self, page: Page):
        """FRONT-05 : Le titre de la section active est 'Sessions actives' (pas 'Module Code actif')."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(2000)

        html = page.content()
        assert "Module Code actif" not in html, \
            "Ancien titre 'Module Code actif' présent — FRONT-05 non appliqué"

    def test_section_active_pipeline_existe(self, page: Page):
        """#active-pipeline-section est présent dans le DOM du dashboard."""
        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(3000)

        section = page.query_selector("#active-pipeline-section")
        assert section is not None, "#active-pipeline-section absent du dashboard"

    def test_waiting_banner_visible_si_sessions_waiting(self, page: Page):
        """Si des sessions WAITING_VALIDATION existent, le banner orange s'affiche."""
        # Vérifier s'il y a des sessions WAITING_VALIDATION (MC ou Atelier)
        projects = requests.get(f"{API_BASE}/projects/").json()
        mc_waiting = any(
            s["status"] == "WAITING_VALIDATION"
            for p in projects
            for s in requests.get(f"{API_BASE}/projects/{p['id']}/sessions").json()
        )
        atelier_waiting = any(
            p.get("session_status") == "WAITING_VALIDATION"
            for p in requests.get(f"{API_BASE}/atelier/prospects").json()
        )

        if not mc_waiting and not atelier_waiting:
            pytest.skip("Aucune session WAITING_VALIDATION — impossible de tester le banner")

        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(3000)

        banner = page.query_selector(".waiting-banner")
        assert banner is not None, \
            "Banner .waiting-banner absent malgré des sessions WAITING_VALIDATION"

        banner_text = banner.inner_text()
        assert any(s in banner_text.lower() for s in ["attent", "validation", "⏸"]), \
            f"Texte du banner inattendu : '{banner_text}'"

    def test_dashboard_charge_sans_erreur_apres_front05(self, page: Page):
        """RÉGRESSION : le dashboard charge sans erreur JS après FRONT-05."""
        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/index.html")
        page.wait_for_timeout(3000)

        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS dashboard après FRONT-05 : {critical}"


# ─── FRONT-06 : project.html lancement inline ────────────────────────────────

class TestFront06ProjectInline:
    """
    FRONT-06 : Depuis project.html, les actions de lancement doivent être sans friction.
    "Nouveau Chat" → redirect direct (pas de modal).
    "Nouveau Module Code" → modal avec projet pré-rempli et désactivé.
    Section renommée "Activité du projet".
    """

    def test_section_activite_du_projet_renommee(self, page: Page):
        """'Conversations' renommé en 'Activité du projet' dans project.html (FRONT-06)."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")

        page.goto(f"{BASE_URL}/project.html?id={project_id}")
        page.wait_for_timeout(2500)

        html = page.content()
        assert "Activité du projet" in html, \
            "Section non renommée : 'Activité du projet' absent de project.html (FRONT-06)"

    def test_nouveau_chat_sans_modal(self, page: Page):
        """'Nouveau Chat' depuis project.html → pas de modal (création directe)."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")

        page.goto(f"{BASE_URL}/project.html?id={project_id}")
        page.wait_for_timeout(2500)

        btn = page.query_selector("#btn-project-new-chat")
        assert btn is not None, "#btn-project-new-chat absent sur project.html"

        # Intercepter les appels API
        api_calls = []
        page.on("request", lambda req: api_calls.append(req.url) if "/api/chat/conversations" in req.url else None)

        btn.click()
        page.wait_for_timeout(500)  # Court délai pour voir si modal apparaît

        # Vérifier qu'aucune modal VISIBLE ne s'est ouverte
        modal = page.query_selector(".modal-overlay")
        if modal:
            is_visible = modal.evaluate(
                "el => el.style.display !== 'none' && el.offsetParent !== null"
            )
            assert not is_visible, (
                "Modal visible après clic 'Nouveau Chat' depuis project.html — "
                "FRONT-06 exige un redirect direct sans modal"
            )

        # Vérifier que le redirect vers chat.html s'est produit
        page.wait_for_timeout(2000)
        assert "chat.html" in page.url, (
            f"Pas de redirect vers chat.html après 'Nouveau Chat' — "
            f"URL actuelle : {page.url}"
        )

    def test_nouveau_module_modal_projet_prerempli(self, page: Page):
        """'Nouveau Module Code' depuis project.html → modal avec projet pré-rempli et disabled."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")

        page.goto(f"{BASE_URL}/project.html?id={project_id}")
        page.wait_for_timeout(2500)

        btn = page.query_selector("#btn-project-new-module")
        assert btn is not None, "#btn-project-new-module absent sur project.html"

        btn.click()
        page.wait_for_timeout(800)

        modal = page.query_selector(".modal-overlay")
        assert modal is not None, "Modal absent après clic 'Nouveau Module Code'"

        # Le select projet doit être disabled (projet déjà connu)
        project_select = modal.query_selector("#modal-module-project")
        if project_select:
            # Utiliser evaluate pour lire la propriété DOM disabled directement
            # (plus fiable que is_disabled() de Playwright pour les attributs injectés via innerHTML)
            is_disabled = project_select.evaluate("el => el.disabled")
            assert is_disabled, (
                "Select projet non désactivé — le projet courant doit être "
                "pré-rempli et grisé (FRONT-06 — sidebar.js handleNewModulePreset)"
            )

        # Fermer le modal proprement
        cancel = modal.query_selector("button.btn-secondary")
        if cancel:
            cancel.click()
            page.wait_for_timeout(300)

    def test_regression_project_html_charge_sans_erreur(self, page: Page):
        """RÉGRESSION FRONT-06 : project.html charge sans erreur JS."""
        project_id = get_first_project_id()
        if not project_id:
            pytest.skip("Aucun projet disponible")

        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/project.html?id={project_id}")
        page.wait_for_timeout(3000)

        critical = [e for e in js_errors if any(x in e.lower() for x in ["typeerror", "referenceerror", "cannot read"])]
        assert len(critical) == 0, f"Erreurs JS project.html après FRONT-06 : {critical}"
