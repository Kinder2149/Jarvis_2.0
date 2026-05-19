"""
Tests live — Agent MENTOR via JARVIS Orchestrateur.
Vérifie : routing, session réflexion, continuité de session, maturation.
Prérequis : serveur actif sur localhost:8000
Lancement : pytest tests/live/test_jarvis_mentor.py -m live -v --timeout=120
"""
import pytest
from tests.live.conftest_jarvis import chat, jarvis_api, assert_valid_response

pytestmark = pytest.mark.live


class TestMentorRouting:
    """JARVIS route correctement vers MENTOR pour les missions."""

    def test_mission_code_route_vers_mentor(self, conv):
        res = chat(conv, "Je veux analyser mon projet et définir une mission de développement.")
        assert_valid_response(res, expected_agents=["MENTOR", "JARVIS"])

    def test_livrable_route_vers_mentor(self, conv):
        res = chat(conv, "Je veux créer un livrable pour mon projet code.")
        assert_valid_response(res, expected_agents=["MENTOR", "JARVIS"])

    def test_force_mentor_sans_projet(self, conv):
        """MENTOR répond même sans projet — explique qu'il faut un projet ou pose des questions."""
        res = chat(conv, "Bonjour.", force_agent="MENTOR")
        assert res["agent"] == "MENTOR"
        assert_valid_response(res)


class TestMentorSessionReflexion:
    """MENTOR crée et gère une session de réflexion."""

    def test_mentor_cree_session_reflexion(self, conv_with_project):
        """Premier message → MENTOR crée une session réflexion (instance_ref présent)."""
        c = conv_with_project
        res = chat(c["conv_id"], "Analysons ce projet et définissons une mission.", force_agent="MENTOR")
        assert res["agent"] == "MENTOR"
        assert_valid_response(res)
        assert res.get("instance_ref") is not None, "instance_ref absent"
        assert res["instance_ref"]["type"] == "reflexion", (
            f"Type attendu 'reflexion', obtenu : {res['instance_ref']}"
        )
        assert isinstance(res["instance_ref"]["id"], int), "ID de session réflexion invalide"

    def test_mentor_continue_meme_session(self, conv_with_project):
        """Deux messages consécutifs → même session réflexion (même ID)."""
        c = conv_with_project
        res1 = chat(c["conv_id"], "Je veux améliorer la fonction hello() dans main.py.", force_agent="MENTOR")
        assert res1.get("instance_ref") is not None, "instance_ref absent au message 1"
        session_id_1 = res1["instance_ref"]["id"]

        res2 = chat(c["conv_id"], "Quels critères de succès pour cette mission ?", force_agent="MENTOR")
        assert res2.get("instance_ref") is not None, "instance_ref absent au message 2"
        session_id_2 = res2["instance_ref"]["id"]

        assert session_id_1 == session_id_2, (
            f"Session changée entre les messages : {session_id_1} → {session_id_2}"
        )

    def test_mentor_repond_en_francais_coherent(self, conv_with_project):
        """La réponse de MENTOR est du texte lisible, pas du JSON brut ni une erreur."""
        c = conv_with_project
        res = chat(c["conv_id"], "Qu'est-ce que ce projet contient comme fichiers ?", force_agent="MENTOR")
        assert res["agent"] == "MENTOR"
        assert_valid_response(res)
        content = res["content"]
        assert not content.strip().startswith("{"), f"Réponse JSON brute inattendue : {content[:100]}"
        assert not content.lower().startswith("error"), f"Erreur retournée : {content[:100]}"

    def test_mentor_suggest_freeze_est_booleen(self, conv_with_project):
        """suggest_freeze doit toujours être un booléen dans la réponse MENTOR."""
        c = conv_with_project
        res = chat(c["conv_id"], "Je veux ajouter une fonction add() dans utils.py.", force_agent="MENTOR")
        assert res["agent"] == "MENTOR"
        assert isinstance(res.get("suggest_freeze"), bool), (
            f"suggest_freeze absent ou invalide : {res.get('suggest_freeze')}"
        )

    def test_mentor_maturation_plusieurs_echanges(self, conv_with_project):
        """Après 3+ échanges sur la même mission, suggest_freeze peut devenir True."""
        c = conv_with_project
        chat(c["conv_id"], "Je veux ajouter une fonction add() dans utils.py.", force_agent="MENTOR")
        chat(c["conv_id"], "La fonction doit additionner deux entiers et retourner le résultat.", force_agent="MENTOR")
        chat(c["conv_id"], "Critères : gérer les valeurs None, renvoyer 0 dans ce cas.", force_agent="MENTOR")
        res = chat(c["conv_id"], "La mission est bien définie, peut-on la figer ?", force_agent="MENTOR")

        assert res["agent"] == "MENTOR"
        assert_valid_response(res)
        # suggest_freeze est bool — True si Gemini juge la mission mature
        assert isinstance(res.get("suggest_freeze"), bool)
        # La réponse doit parler de mission, figement ou livrable
        content_lower = res["content"].lower()
        assert any(
            word in content_lower
            for word in ["mission", "figer", "livrable", "critères", "défini", "prêt"]
        ), f"Réponse MENTOR hors sujet : {res['content'][:200]}"


class TestMentorStructureReponse:
    """Structure complète de la réponse MENTOR."""

    def test_champs_obligatoires_presents(self, conv_with_project):
        c = conv_with_project
        res = chat(c["conv_id"], "Analysons le projet.", force_agent="MENTOR")
        assert "agent" in res and res["agent"] == "MENTOR"
        assert "content" in res and res["content"]
        assert "instance_ref" in res
        assert "suggest_freeze" in res
        assert "routing_info" in res
        ri = res["routing_info"]
        assert "agent" in ri
        assert "confidence" in ri
        assert isinstance(ri["confidence"], (int, float))

    def test_session_reflexion_existe_en_base(self, conv_with_project):
        """La session réflexion créée par MENTOR est bien persistée en base."""
        c = conv_with_project
        res = chat(c["conv_id"], "Définissons une mission pour ce projet.", force_agent="MENTOR")
        assert res.get("instance_ref") is not None
        session_id = res["instance_ref"]["id"]

        # Vérifier via l'API réflexions que la session existe
        session = jarvis_api("get", f"/reflexions/{session_id}")
        assert session["id"] == session_id
        assert session["statut"] in ("OUVERTE", "FIGEE"), (
            f"Statut inattendu : {session['statut']}"
        )
