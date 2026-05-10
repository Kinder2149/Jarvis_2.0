"""
Tests d'intégration — routes /api/sentinelle
Couvre : positions, watchlist, cycles, transactions, budget.
Les skills IA (veille, analyse, propositions, ordre) ne sont pas testés ici
car ils appellent de vrais modèles — coût et réseau non maîtrisés.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client(temp_db_path):
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            yield c


# ─── Positions ────────────────────────────────────────────────────────────────

class TestPositions:

    def test_liste_vide_au_depart(self, client):
        r = client.get("/api/sentinelle/positions")
        assert r.status_code == 200
        assert r.json() == []

    def test_creer_position(self, client):
        r = client.post("/api/sentinelle/positions", json={
            "ticker": "VWCE", "quantite": 5.0, "enveloppe": "PEA", "date_entree": "2026-05-01"
        })
        assert r.status_code == 201
        data = r.json()
        assert data["ticker"] == "VWCE"
        assert data["quantite"] == 5.0
        assert data["enveloppe"] == "PEA"

    def test_liste_retourne_position_creee(self, client):
        client.post("/api/sentinelle/positions", json={
            "ticker": "IWDA", "quantite": 3.0, "enveloppe": "CTO", "date_entree": "2026-05-01"
        })
        data = client.get("/api/sentinelle/positions").json()
        assert len(data) == 1
        assert data[0]["ticker"] == "IWDA"

    def test_mettre_a_jour_quantite(self, client):
        r = client.post("/api/sentinelle/positions", json={
            "ticker": "BTC", "quantite": 0.001, "enveloppe": "CTO", "date_entree": "2026-05-01"
        })
        pid = r.json()["id"]
        r2 = client.put(f"/api/sentinelle/positions/{pid}", json={"quantite": 0.002})
        assert r2.status_code == 200
        assert r2.json()["quantite"] == 0.002

    def test_mise_a_jour_position_inexistante(self, client):
        r = client.put("/api/sentinelle/positions/9999", json={"quantite": 1.0})
        assert r.status_code == 404

    def test_supprimer_position(self, client):
        r = client.post("/api/sentinelle/positions", json={
            "ticker": "ETH", "quantite": 0.5, "enveloppe": "CTO", "date_entree": "2026-05-01"
        })
        pid = r.json()["id"]
        r2 = client.delete(f"/api/sentinelle/positions/{pid}")
        assert r2.status_code == 204
        assert client.get("/api/sentinelle/positions").json() == []

    def test_supprimer_position_inexistante(self, client):
        r = client.delete("/api/sentinelle/positions/9999")
        assert r.status_code == 404


# ─── Watchlist ────────────────────────────────────────────────────────────────

class TestWatchlist:

    def test_liste_vide_au_depart(self, client):
        r = client.get("/api/sentinelle/watchlist")
        assert r.status_code == 200
        assert r.json() == []

    def test_ajouter_actif(self, client):
        r = client.post("/api/sentinelle/watchlist", json={
            "ticker": "SOL", "niveau_risque": "speculatif"
        })
        assert r.status_code == 201
        assert r.json()["ticker"] == "SOL"

    def test_ticker_duplique_renvoie_400(self, client):
        client.post("/api/sentinelle/watchlist", json={"ticker": "SOL", "niveau_risque": "modere"})
        r = client.post("/api/sentinelle/watchlist", json={"ticker": "SOL", "niveau_risque": "faible"})
        assert r.status_code == 400

    def test_retirer_actif(self, client):
        r = client.post("/api/sentinelle/watchlist", json={"ticker": "ADA", "niveau_risque": "eleve"})
        wid = r.json()["id"]
        r2 = client.delete(f"/api/sentinelle/watchlist/{wid}")
        assert r2.status_code == 204
        assert client.get("/api/sentinelle/watchlist").json() == []

    def test_retirer_actif_inexistant(self, client):
        r = client.delete("/api/sentinelle/watchlist/9999")
        assert r.status_code == 404


# ─── Cycles ───────────────────────────────────────────────────────────────────

class TestCycles:

    def test_liste_vide_au_depart(self, client):
        assert client.get("/api/sentinelle/cycles").json() == []

    def test_cycle_actif_null_si_aucun(self, client):
        r = client.get("/api/sentinelle/cycles/actif")
        assert r.status_code == 200
        assert r.json() is None

    def test_creer_cycle(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05", "budget_mensuel": 20.0})
        assert r.status_code == 201
        data = r.json()
        assert data["mois"] == "2026-05"
        assert data["etat"] == "PHASE_1"
        assert data["budget_mensuel"] == 20.0

    def test_cycle_actif_retourne_cycle_en_cours(self, client):
        client.post("/api/sentinelle/cycles", json={"mois": "2026-05", "budget_mensuel": 20.0})
        r = client.get("/api/sentinelle/cycles/actif")
        assert r.json() is not None
        assert r.json()["etat"] == "PHASE_1"

    def test_ne_peut_pas_creer_deux_cycles_ouverts(self, client):
        client.post("/api/sentinelle/cycles", json={"mois": "2026-05", "budget_mensuel": 20.0})
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05", "budget_mensuel": 20.0})
        assert r.status_code == 400

    def test_transition_etat_valide(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05"})
        cid = r.json()["id"]
        r2 = client.patch(f"/api/sentinelle/cycles/{cid}/etat", json={"etat": "PHASE_2"})
        assert r2.status_code == 200
        assert r2.json()["etat"] == "PHASE_2"

    def test_transition_etat_invalide_renvoie_400(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05"})
        cid = r.json()["id"]
        r2 = client.patch(f"/api/sentinelle/cycles/{cid}/etat", json={"etat": "PHASE_4"})
        assert r2.status_code == 400

    def test_transition_cycle_inexistant(self, client):
        r = client.patch("/api/sentinelle/cycles/9999/etat", json={"etat": "PHASE_2"})
        assert r.status_code == 404

    def test_enregistrer_decision(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05"})
        cid = r.json()["id"]
        r2 = client.patch(f"/api/sentinelle/cycles/{cid}/decision", json={
            "mode": "accumulation", "decision": "Accumulation"
        })
        assert r2.status_code == 200
        data = r2.json()
        assert data["mode"] == "accumulation"
        assert data["decision"] == "Accumulation"

    def test_cloture_cycle(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05"})
        cid = r.json()["id"]
        r2 = client.patch(f"/api/sentinelle/cycles/{cid}/cloture", json={})
        assert r2.status_code == 200
        assert r2.json()["etat"] == "CLOTURE"

    def test_cloture_cycle_deja_cloture_renvoie_400(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05"})
        cid = r.json()["id"]
        client.patch(f"/api/sentinelle/cycles/{cid}/cloture", json={})
        r2 = client.patch(f"/api/sentinelle/cycles/{cid}/cloture", json={})
        assert r2.status_code == 400

    def test_apres_cloture_nouveau_cycle_possible(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05"})
        cid = r.json()["id"]
        client.patch(f"/api/sentinelle/cycles/{cid}/cloture", json={})
        r2 = client.post("/api/sentinelle/cycles", json={"mois": "2026-06"})
        assert r2.status_code == 201


# ─── Transactions ─────────────────────────────────────────────────────────────

class TestTransactions:

    def _cycle(self, client):
        r = client.post("/api/sentinelle/cycles", json={"mois": "2026-05"})
        return r.json()["id"]

    def test_liste_vide_au_depart(self, client):
        assert client.get("/api/sentinelle/transactions").json() == []

    def test_creer_transaction(self, client):
        cid = self._cycle(client)
        r = client.post("/api/sentinelle/transactions", json={
            "cycle_id": cid, "ticker": "VWCE", "quantite": 2.0,
            "prix_reel": 110.5, "frais": 1.0, "date_transaction": "2026-05-10"
        })
        assert r.status_code == 201
        data = r.json()
        assert data["ticker"] == "VWCE"
        assert data["prix_reel"] == 110.5

    def test_transaction_cycle_inexistant(self, client):
        r = client.post("/api/sentinelle/transactions", json={
            "cycle_id": 9999, "ticker": "BTC", "quantite": 0.001,
            "prix_reel": 50000.0, "frais": 1.0, "date_transaction": "2026-05-10"
        })
        assert r.status_code == 404

    def test_filtrage_par_cycle(self, client):
        cid = self._cycle(client)
        client.post("/api/sentinelle/transactions", json={
            "cycle_id": cid, "ticker": "ETH", "quantite": 0.1,
            "prix_reel": 3000.0, "frais": 1.0, "date_transaction": "2026-05-10"
        })
        data = client.get(f"/api/sentinelle/transactions?cycle_id={cid}").json()
        assert len(data) == 1
        assert data[0]["ticker"] == "ETH"


# ─── Budget ───────────────────────────────────────────────────────────────────

class TestBudget:

    def test_budget_sans_cycle_renvoie_zeros(self, client):
        r = client.get("/api/sentinelle/budget/2026-05")
        assert r.status_code == 200
        data = r.json()
        assert data["budget_restant"] == 0.0

    def test_budget_avec_cycle(self, client):
        client.post("/api/sentinelle/cycles", json={"mois": "2026-05", "budget_mensuel": 20.0})
        r = client.get("/api/sentinelle/budget/2026-05")
        data = r.json()
        assert data["budget_mensuel"] == 20.0
        assert data["budget_utilise"] == 0.0
        assert data["budget_restant"] == 20.0
