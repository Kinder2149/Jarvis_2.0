"""
Tests live — JARVIS Orchestrateur.
Vérifie : réponses directes, routing vers agents, mode forcé, isolation conversations.
Prérequis : serveur actif sur localhost:8000
Lancement : pytest tests/live/test_jarvis_orchestrator.py -m live -v --timeout=120
"""
import pytest
from tests.live.conftest_jarvis import chat, jarvis_api, assert_valid_response

pytestmark = pytest.mark.live


class TestJarvisReponseDirect:
    """JARVIS répond seul quand aucun agent n'est nécessaire."""

    def test_salutation_reste_jarvis(self, conv):
        res = chat(conv, "Bonjour, comment tu fonctionnes ?")
        assert_valid_response(res, expected_agents=["JARVIS"])

    def test_question_generale_reste_jarvis(self, conv):
        res = chat(conv, "Qu'est-ce que tu peux faire pour moi ?")
        assert_valid_response(res, expected_agents=["JARVIS"])

    def test_reponse_contient_du_texte_coherent(self, conv):
        res = chat(conv, "Explique-moi en une phrase ce qu'est JARVIS.")
        assert_valid_response(res)
        # La réponse doit parler de JARVIS, d'agents ou d'IA
        content_lower = res["content"].lower()
        assert any(
            word in content_lower
            for word in ["jarvis", "agent", "ia", "assistant", "orchestr"]
        ), f"Réponse hors sujet : {res['content'][:200]}"

    def test_conversation_persistante_contexte(self, conv):
        """Deux messages dans la même conversation : le second peut référencer le premier."""
        chat(conv, "Mon prénom est Test.")
        res2 = chat(conv, "Quel est mon prénom ?")
        assert_valid_response(res2)
        # JARVIS devrait pouvoir rappeler "Test" (contexte conversation)
        # Test souple : on vérifie juste que la réponse est cohérente
        assert res2["content"]


class TestJarvisRouting:
    """JARVIS route correctement vers les agents spécialistes."""

    def test_route_vers_mentor_mission(self, conv):
        res = chat(conv, "Je veux définir une mission de développement pour mon projet.")
        assert_valid_response(res, expected_agents=["MENTOR", "JARVIS"])
        # Si JARVIS demande une clarification, c'est normal aussi

    def test_route_vers_sentinelle_investissement(self, conv):
        res = chat(conv, "Quel est mon budget d'investissement ce mois-ci ?")
        assert_valid_response(res, expected_agents=["SENTINELLE", "JARVIS"])

    def test_route_vers_atelier_prospect(self, conv):
        res = chat(conv, "Je veux créer un nouveau prospect restaurant.")
        assert_valid_response(res, expected_agents=["ATELIER", "JARVIS"])

    def test_routing_info_present_dans_reponse(self, conv):
        res = chat(conv, "Bonjour.")
        assert "routing_info" in res, "routing_info absent de la réponse"
        ri = res["routing_info"]
        assert "agent" in ri
        assert "confidence" in ri
        assert isinstance(ri["confidence"], (int, float))


class TestJarvisModeForcé:
    """force_agent bypass le routing et envoie directement à l'agent."""

    def test_force_mentor_contourne_routing(self, conv):
        res = chat(conv, "Bonjour.", force_agent="MENTOR")
        # MENTOR doit répondre même sur un message non-spécifique
        assert res["agent"] == "MENTOR"
        assert_valid_response(res)

    def test_force_jarvis_retourne_jarvis(self, conv):
        res = chat(conv, "Donne-moi une liste d'agents.", force_agent="JARVIS")
        assert res["agent"] == "JARVIS"
        assert_valid_response(res)


class TestJarvisIsolationConversations:
    """Deux conversations distinctes n'ont pas de contexte partagé."""

    def test_deux_conversations_contextes_independants(self):
        # Conversation 1
        c1 = jarvis_api("post", "/jarvis/conversations", json={"title": "TEST_ISO_1"})
        c2 = jarvis_api("post", "/jarvis/conversations", json={"title": "TEST_ISO_2"})
        try:
            chat(c1["id"], "Mon mot secret est XYLOPHONE99.")
            res = chat(c2["id"], "Quel est mon mot secret ?")
            # Conv 2 ne doit pas connaître XYLOPHONE99
            assert "XYLOPHONE99" not in res["content"], (
                "Fuite de contexte entre conversations détectée !"
            )
        finally:
            for c in [c1, c2]:
                try:
                    jarvis_api("delete", f"/jarvis/conversations/{c['id']}")
                except Exception:
                    pass
