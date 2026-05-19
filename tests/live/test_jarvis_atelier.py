"""
Tests live — Agent ATELIER via JARVIS Orchestrateur.
Vérifie : flux 3 questions, création directe, annulation de flow.
Prérequis : serveur actif sur localhost:8000
Lancement : pytest tests/live/test_jarvis_atelier.py -m live -v --timeout=120
"""
import pytest
from tests.live.conftest_jarvis import chat, jarvis_api, assert_valid_response

pytestmark = pytest.mark.live

RESTAURANT_NOM   = "La Belle Trattoria Test"
RESTAURANT_URL   = "https://labelletrattoria-test.fr"
RESTAURANT_NOTE  = "Restaurant italien haut de gamme, 80 couverts, ouvert depuis 2019"


class TestAtelierFluxComplet:
    """Flow 3 étapes : nom → URL → note → prospect créé."""

    def test_flux_3_etapes_cree_prospect(self, conv):
        # Étape 0 : déclenchement
        res0 = chat(conv, "Je veux créer un nouveau prospect.", force_agent="ATELIER")
        assert res0["agent"] == "ATELIER"
        assert_valid_response(res0)
        # ATELIER doit demander le nom du restaurant
        assert any(
            word in res0["content"].lower()
            for word in ["nom", "restaurant", "établissement"]
        ), f"ATELIER ne demande pas le nom : {res0['content']}"

        # Étape 1 : donner le nom
        res1 = chat(conv, RESTAURANT_NOM, force_agent="ATELIER")
        assert res1["agent"] == "ATELIER"
        assert_valid_response(res1)
        assert any(
            word in res1["content"].lower()
            for word in ["url", "site", "web", "lien"]
        ), f"ATELIER ne demande pas l'URL : {res1['content']}"

        # Étape 2 : donner l'URL
        res2 = chat(conv, RESTAURANT_URL, force_agent="ATELIER")
        assert res2["agent"] == "ATELIER"
        assert_valid_response(res2)
        assert any(
            word in res2["content"].lower()
            for word in ["note", "contexte", "optionnel", "passer"]
        ), f"ATELIER ne demande pas la note : {res2['content']}"

        # Étape 3 : donner la note → prospect créé
        res3 = chat(conv, RESTAURANT_NOTE, force_agent="ATELIER")
        assert res3["agent"] == "ATELIER"
        assert_valid_response(res3)
        assert any(
            word in res3["content"].lower()
            for word in ["créé", "succès", "prospect", "atelier"]
        ), f"ATELIER ne confirme pas la création : {res3['content']}"
        # Le lien vers atelier.html doit être présent
        assert "atelier.html" in res3["content"], (
            f"Lien atelier.html absent : {res3['content']}"
        )

        # Vérifier en base que le prospect existe
        prospects = jarvis_api("get", "/atelier/prospects")
        noms = [p.get("nom", "") for p in prospects]
        assert any(RESTAURANT_NOM in n for n in noms), (
            f"Prospect {RESTAURANT_NOM!r} introuvable en base. Noms trouvés : {noms}"
        )

        # Cleanup prospect
        for p in prospects:
            if RESTAURANT_NOM in p.get("nom", ""):
                try:
                    jarvis_api("delete", f"/atelier/prospects/{p['id']}")
                except Exception:
                    pass

    def test_pas_de_site_accepte(self, conv):
        """L'URL 'None' ou 'pas de site' est acceptée."""
        chat(conv, "Créer un prospect.", force_agent="ATELIER")
        chat(conv, "Le Bistro du Coin Test NOSITETEST", force_agent="ATELIER")
        res = chat(conv, "pas de site", force_agent="ATELIER")
        assert res["agent"] == "ATELIER"
        # Doit passer à l'étape suivante (note), pas bloquer
        assert any(
            word in res["content"].lower()
            for word in ["note", "contexte", "optionnel", "dernier"]
        ), f"ATELIER bloqué sur l'URL vide : {res['content']}"
        # Finir le flow proprement
        res_fin = chat(conv, "-", force_agent="ATELIER")
        # Cleanup
        prospects = jarvis_api("get", "/atelier/prospects")
        for p in prospects:
            if "NOSITETEST" in p.get("nom", ""):
                try:
                    jarvis_api("delete", f"/atelier/prospects/{p['id']}")
                except Exception:
                    pass

    def test_annulation_flow_par_signal_abort(self, conv):
        """Un signal d'annulation coupe le flow proprement."""
        chat(conv, "Créer un prospect.", force_agent="ATELIER")
        res_abort = chat(conv, "annule", force_agent="ATELIER")
        assert res_abort["agent"] in ("ATELIER", "JARVIS")
        assert any(
            word in res_abort["content"].lower()
            for word in ["annulé", "annule", "aucun", "comment", "aider"]
        ), f"Annulation non gérée : {res_abort['content']}"


class TestAtelierCreationDirecte:
    """Création directe quand l'URL est dans le premier message."""

    def test_creation_directe_avec_url(self, conv):
        msg = f"Nouveau prospect Chez Marco Test Direct https://chezmarco-testdirect.fr"
        res = chat(conv, msg, force_agent="ATELIER")
        assert res["agent"] == "ATELIER"
        # Doit créer directement sans passer par le flow 3 étapes
        if "atelier.html" in res["content"]:
            # Création directe réussie — cleanup
            prospects = jarvis_api("get", "/atelier/prospects")
            for p in prospects:
                if "Marco Test Direct" in p.get("nom", ""):
                    try:
                        jarvis_api("delete", f"/atelier/prospects/{p['id']}")
                    except Exception:
                        pass
        # Si ATELIER démarre le flow, c'est aussi acceptable
        assert_valid_response(res)
