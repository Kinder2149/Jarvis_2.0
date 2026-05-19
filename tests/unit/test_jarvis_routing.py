"""
Tests unitaires — logique de routing JARVIS (sans LLM).
Couvre : _route_heuristique, _should_skip_routing, _get_agent_actif.
"""
import pytest


class TestRouteHeuristique:

    def _agents(self):
        """Liste d'agents minimaliste pour les tests."""
        return [
            {"name": "MENTOR", "routing_hints": '["réflexion", "mission", "plan", "analyse", "penser"]'},
            {"name": "FORGE", "routing_hints": '["pipeline", "exécuter", "démarrer", "code", "lancer"]'},
            {"name": "SENTINELLE", "routing_hints": '["budget", "portefeuille", "investissement", "position", "ticker"]'},
            {"name": "ATELIER", "routing_hints": '["prospect", "restaurant", "client", "atelier"]'},
            {"name": "JARVIS", "routing_hints": '[]'},
        ]

    def test_message_vide_retourne_jarvis(self):
        from backend.services.jarvis_service import _route_heuristique
        result = _route_heuristique("", self._agents())
        assert result.get("agent") == "JARVIS"

    def test_message_court_retourne_jarvis(self):
        from backend.services.jarvis_service import _route_heuristique
        result = _route_heuristique("ok", self._agents())
        assert result.get("agent") == "JARVIS"

    def test_un_mot_cle_ne_route_pas(self):
        from backend.services.jarvis_service import _route_heuristique
        result = _route_heuristique("réflexion", self._agents())
        # Seuil >= 2, donc ne devrait pas router
        assert result.get("agent") == "JARVIS"

    def test_deux_mots_cles_mentor_route(self):
        from backend.services.jarvis_service import _route_heuristique
        result = _route_heuristique("je veux une réflexion pour ma mission", self._agents())
        assert result.get("agent") == "MENTOR"

    def test_deux_mots_cles_sentinelle_route(self):
        from backend.services.jarvis_service import _route_heuristique
        result = _route_heuristique("quel est mon budget pour le portefeuille ?", self._agents())
        assert result.get("agent") == "SENTINELLE"

    def test_nom_agent_explicite_retourne_jarvis(self):
        from backend.services.jarvis_service import _route_heuristique
        result = _route_heuristique("MENTOR aide-moi", self._agents())
        # Message court, retourne JARVIS
        assert result.get("agent") == "JARVIS"


class TestShouldSkipRouting:

    def test_message_court_skip(self):
        from backend.services.jarvis_service import _should_skip_routing
        result = _should_skip_routing("ok merci", "MENTOR")
        assert result is True

    def test_signal_changement_ne_skip_pas(self):
        from backend.services.jarvis_service import _should_skip_routing
        result = _should_skip_routing("maintenant parle-moi de SENTINELLE", "MENTOR")
        assert result is False

    def test_message_normal_sans_signal_skip(self):
        from backend.services.jarvis_service import _should_skip_routing
        result = _should_skip_routing("continue sur ce sujet s'il te plaît", "MENTOR")
        assert result is True

    def test_autre_chose_ne_skip_pas(self):
        from backend.services.jarvis_service import _should_skip_routing
        result = _should_skip_routing("autre chose : mon budget", "SENTINELLE")
        assert result is False

    def test_jarvis_actif_ne_skip_jamais(self):
        from backend.services.jarvis_service import _should_skip_routing
        # Quand JARVIS est actif, on route toujours (pas de continuation à préserver)
        result = _should_skip_routing("bonjour comment ça va", "JARVIS")
        assert result is False


class TestGetAgentActif:

    def test_retourne_jarvis_si_aucun_message(self):
        from backend.services.jarvis_service import _get_agent_actif
        result = _get_agent_actif([])
        # Peut retourner None ou "JARVIS" selon implémentation
        assert result is None or result == "JARVIS"

    def test_retourne_agent_du_dernier_message_assistant(self):
        from backend.services.jarvis_service import _get_agent_actif
        messages = [
            {"role": "user", "content": "test", "agent": None},
            {"role": "assistant", "content": "réponse MENTOR", "agent": "MENTOR"},
        ]
        result = _get_agent_actif(messages)
        assert result == "MENTOR"

    def test_ignore_messages_user(self):
        from backend.services.jarvis_service import _get_agent_actif
        messages = [
            {"role": "assistant", "content": "...", "agent": "FORGE"},
            {"role": "user", "content": "...", "agent": None},
        ]
        result = _get_agent_actif(messages)
        assert result == "FORGE"

    def test_retourne_none_si_pas_de_message_assistant(self):
        from backend.services.jarvis_service import _get_agent_actif
        messages = [
            {"role": "user", "content": "premier message", "agent": None},
        ]
        result = _get_agent_actif(messages)
        # Peut retourner None ou "JARVIS" selon implémentation
        assert result is None or result == "JARVIS"
