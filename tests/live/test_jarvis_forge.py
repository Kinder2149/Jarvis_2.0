"""
Tests live — Agent FORGE via JARVIS Orchestrateur.
Vérifie : routing, status query sans livrable, structure de réponse.
Note : Le flux complet MENTOR→FORGE (figement + lancement pipeline) requiert
       un livrable figé réel — couvert par SCENARIOS_MANUELS.md.
Prérequis : serveur actif sur localhost:8000
Lancement : pytest tests/live/test_jarvis_forge.py -m live -v --timeout=120
"""
import pytest
from tests.live.conftest_jarvis import chat, jarvis_api, assert_valid_response

pytestmark = pytest.mark.live


class TestForgeRouting:
    """JARVIS route correctement vers FORGE."""

    def test_pipeline_route_vers_forge(self, conv):
        res = chat(conv, "Lance le pipeline pour ma mission code.")
        assert_valid_response(res, expected_agents=["FORGE", "JARVIS"])

    def test_forge_exécute_route_vers_forge(self, conv):
        res = chat(conv, "Exécute ma mission de développement.")
        assert_valid_response(res, expected_agents=["FORGE", "MENTOR", "JARVIS"])

    def test_force_forge_repond(self, conv):
        """FORGE répond quand forcé, même sans contexte de mission."""
        res = chat(conv, "Quel est l'état du pipeline ?", force_agent="FORGE")
        assert res["agent"] == "FORGE"
        assert_valid_response(res)

    def test_force_forge_sans_livrable_est_explicatif(self, conv):
        """Sans livrable disponible, FORGE explique le workflow attendu."""
        res = chat(conv, "Je veux lancer FORGE.", force_agent="FORGE")
        assert res["agent"] == "FORGE"
        assert_valid_response(res)
        content_lower = res["content"].lower()
        assert any(
            word in content_lower
            for word in ["mission", "livrable", "mentor", "pipeline", "forge", "projet"]
        ), f"Réponse FORGE hors sujet : {res['content'][:200]}"

    def test_force_forge_pas_derreur_serveur(self, conv):
        """FORGE ne doit jamais retourner une traceback Python ou une erreur 500."""
        res = chat(conv, "Statut pipeline.", force_agent="FORGE")
        assert res["agent"] == "FORGE"
        content = res["content"]
        assert not content.lower().startswith("error"), f"Erreur serveur exposée : {content[:100]}"
        assert "traceback" not in content.lower(), f"Traceback exposé : {content[:100]}"


class TestForgeAvecProjet:
    """FORGE avec un projet lié à la conversation (pas de livrable figé)."""

    def test_forge_projet_sans_livrable_repond(self, conv_with_project):
        """Avec un projet mais sans livrable figé, FORGE répond de façon cohérente."""
        c = conv_with_project
        res = chat(c["conv_id"], "Lance le pipeline.", force_agent="FORGE")
        assert res["agent"] == "FORGE"
        assert_valid_response(res)
        # Pas d'erreur serveur
        assert not res["content"].lower().startswith("error"), (
            f"Erreur serveur : {res['content'][:100]}"
        )

    def test_forge_status_sans_pipeline_actif(self, conv_with_project):
        """Sans pipeline actif, FORGE donne un état neutre ou explicatif."""
        c = conv_with_project
        res = chat(c["conv_id"], "Quel est le statut de mon pipeline ?", force_agent="FORGE")
        assert res["agent"] == "FORGE"
        assert_valid_response(res)

    def test_forge_instance_ref_absent_sans_pipeline(self, conv_with_project):
        """Sans pipeline actif, instance_ref est None ou absent."""
        c = conv_with_project
        res = chat(c["conv_id"], "Statut ?", force_agent="FORGE")
        assert res["agent"] == "FORGE"
        # instance_ref peut être None (pas de pipeline en cours)
        assert res.get("instance_ref") is None or res["instance_ref"].get("type") == "pipeline", (
            f"instance_ref inattendu : {res.get('instance_ref')}"
        )


class TestForgeStructureReponse:
    """Structure complète de la réponse FORGE."""

    def test_champs_obligatoires_presents(self, conv):
        res = chat(conv, "Statut pipeline ?", force_agent="FORGE")
        assert "agent" in res and res["agent"] == "FORGE"
        assert "content" in res and res["content"]
        assert "routing_info" in res
        ri = res["routing_info"]
        assert "agent" in ri
        assert "confidence" in ri
        assert isinstance(ri["confidence"], (int, float))

    def test_suggest_freeze_est_false_sans_mission(self, conv):
        """FORGE ne suggère jamais de figement (c'est le rôle de MENTOR)."""
        res = chat(conv, "Lance le pipeline.", force_agent="FORGE")
        assert res["agent"] == "FORGE"
        # FORGE ne suggère pas de figement
        assert res.get("suggest_freeze") in (False, None), (
            f"suggest_freeze inattendu pour FORGE : {res.get('suggest_freeze')}"
        )
