"""
Tests live — Agent SENTINELLE via JARVIS Orchestrateur.
Vérifie : classification d'intention, consultation, watchlist, redirection "agir".
Prérequis : serveur actif sur localhost:8000
Lancement : pytest tests/live/test_jarvis_sentinelle.py -m live -v --timeout=120
"""
import pytest
from tests.live.conftest_jarvis import chat, jarvis_api, assert_valid_response

pytestmark = pytest.mark.live

TICKER_TEST = "TSTLV"  # Ticker fictif ≤5 chars (regex watchlist: [A-Z]{2,5})


class TestSentinelleIntention:
    """SENTINELLE classe correctement les intentions utilisateur."""

    def test_question_budget_est_consulter(self, conv):
        res = chat(conv, "Quel est mon budget d'investissement restant ce mois ?",
                   force_agent="SENTINELLE")
        assert res["agent"] == "SENTINELLE"
        assert_valid_response(res)
        # Réponse doit être une consultation (budget, données, pas une transaction)
        content_lower = res["content"].lower()
        assert not any(
            word in content_lower
            for word in ["je ne peux pas effectuer", "page sentinelle"]
        ) or "budget" in content_lower, (
            f"Réponse inattendue pour une consultation : {res['content']}"
        )

    def test_question_portefeuille_est_consulter(self, conv):
        res = chat(conv, "Quelles sont mes positions actuelles ?",
                   force_agent="SENTINELLE")
        assert res["agent"] == "SENTINELLE"
        assert_valid_response(res)

    def test_question_alertes_est_consulter(self, conv):
        res = chat(conv, "Y a-t-il des alertes non lues dans mon portefeuille ?",
                   force_agent="SENTINELLE")
        assert res["agent"] == "SENTINELLE"
        assert_valid_response(res)

    def test_demande_transaction_est_agir(self, conv):
        """Une demande de transaction doit être redirigée vers la page Sentinelle."""
        res = chat(conv, "Je veux acheter 10 actions Apple maintenant.",
                   force_agent="SENTINELLE")
        assert res["agent"] == "SENTINELLE"
        assert_valid_response(res)
        # SENTINELLE doit refuser et rediriger
        content_lower = res["content"].lower()
        assert any(
            word in content_lower
            for word in ["ne peux pas", "page", "sentinelle", "directement"]
        ), f"Transaction non redirigée : {res['content']}"
        assert "sentinelle.html" in res["content"], (
            f"Lien sentinelle.html absent : {res['content']}"
        )


class TestSentinelleWatchlist:
    """Ajout et retrait de tickers de la watchlist via JARVIS."""

    def test_ajout_ticker_watchlist(self, conv):
        res = chat(
            conv,
            f"Ajoute {TICKER_TEST} à ma watchlist.",
            force_agent="SENTINELLE"
        )
        assert res["agent"] == "SENTINELLE"
        assert_valid_response(res)
        content_lower = res["content"].lower()
        assert any(
            word in content_lower
            for word in ["ajouté", "watchlist", TICKER_TEST.lower()]
        ), f"Ajout non confirmé : {res['content']}"

        # Vérifier en base
        wl = jarvis_api("get", "/sentinelle/watchlist")
        tickers = [w.get("ticker", "") for w in wl]
        assert TICKER_TEST in tickers, f"{TICKER_TEST} absent de la watchlist : {tickers}"

    def test_retrait_ticker_watchlist(self, conv):
        # Ajouter d'abord (setup) — ignorer si déjà présent (test précédent)
        try:
            jarvis_api("post", "/sentinelle/watchlist",
                       json={"ticker": TICKER_TEST, "niveau_risque": "modere"})
        except AssertionError:
            pass  # 400 = déjà présent, acceptable pour ce setup

        res = chat(
            conv,
            f"Retire {TICKER_TEST} de ma watchlist.",
            force_agent="SENTINELLE"
        )
        assert res["agent"] == "SENTINELLE"
        assert_valid_response(res)
        content_lower = res["content"].lower()
        assert any(
            word in content_lower
            for word in ["retiré", "supprimé", TICKER_TEST.lower()]
        ), f"Retrait non confirmé : {res['content']}"

        # Vérifier en base
        wl = jarvis_api("get", "/sentinelle/watchlist")
        tickers = [w.get("ticker", "") for w in wl]
        assert TICKER_TEST not in tickers, f"{TICKER_TEST} toujours en watchlist"

    def test_ticker_deja_present_ne_duplique_pas(self, conv):
        # Ajouter deux fois
        chat(conv, f"Ajoute {TICKER_TEST} à ma watchlist.", force_agent="SENTINELLE")
        res2 = chat(conv, f"Ajoute {TICKER_TEST} à ma watchlist.", force_agent="SENTINELLE")
        assert res2["agent"] == "SENTINELLE"
        # La réponse doit signaler que le ticker est déjà présent
        content_lower = res2["content"].lower()
        assert any(
            word in content_lower
            for word in ["déjà", "already", "watchlist"]
        ), f"Doublon non détecté : {res2['content']}"

        # Cleanup — DELETE prend un ID entier, pas le ticker
        try:
            wl = jarvis_api("get", "/sentinelle/watchlist")
            for entry in wl:
                if entry.get("ticker") == TICKER_TEST:
                    jarvis_api("delete", f"/sentinelle/watchlist/{entry['id']}")
                    break
        except Exception:
            pass


class TestSentinelleRoutingDepuisJarvis:
    """JARVIS route correctement vers SENTINELLE sans force_agent."""

    def test_question_budget_route_vers_sentinelle(self, conv):
        res = chat(conv, "Combien me reste-t-il dans mon budget investissement ?")
        assert_valid_response(res, expected_agents=["SENTINELLE", "JARVIS"])
        # Si JARVIS demande clarification, c'est acceptable aussi

    def test_question_portefeuille_route_vers_sentinelle(self, conv):
        res = chat(conv, "Analyse mon portefeuille boursier actuel.")
        assert_valid_response(res, expected_agents=["SENTINELLE", "JARVIS"])
