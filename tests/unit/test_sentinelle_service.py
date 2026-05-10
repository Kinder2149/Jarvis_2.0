"""
Tests unitaires — sentinelle_service.py
Vérifie la logique budget, carry-over, transitions d'état et calcul transactions.
"""
import sqlite3
import pytest
from unittest.mock import patch


@pytest.fixture
def svc_db(tmp_path):
    """DB SQLite fichier temporaire initialisée avec le vrai schéma."""
    db_path = tmp_path / "test_sentinelle.db"
    with patch("backend.database.DB_PATH", db_path):
        from backend.database import init_db
        init_db()
    yield db_path


def _insert_cycle(db_path, mois, budget_mensuel=20.0, budget_utilise=0.0, etat="PHASE_1"):
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sentinelle_cycles (mois, budget_mensuel, budget_utilise, etat) VALUES (?, ?, ?, ?)",
        (mois, budget_mensuel, budget_utilise, etat)
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid


def _insert_transaction(db_path, cycle_id, quantite, prix_reel, frais=1.0):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO sentinelle_transactions (cycle_id, ticker, quantite, prix_reel, frais, date_transaction) VALUES (?, ?, ?, ?, ?, ?)",
        (cycle_id, "VWCE", quantite, prix_reel, frais, "2026-05-10")
    )
    conn.commit()
    conn.close()


# ─── transition_etat_valide (fonction pure — pas de DB) ───────────────────────

class TestTransitionEtatValide:

    def setup_method(self):
        from backend.services.sentinelle_service import transition_etat_valide
        self.fn = transition_etat_valide

    def test_phase1_vers_phase2(self):
        assert self.fn("PHASE_1", "PHASE_2") is True

    def test_phase2_vers_phase3(self):
        assert self.fn("PHASE_2", "PHASE_3") is True

    def test_phase3_vers_phase4(self):
        assert self.fn("PHASE_3", "PHASE_4") is True

    def test_phase4_vers_phase5_achat(self):
        assert self.fn("PHASE_4", "PHASE_5") is True

    def test_phase4_vers_phase6_accumulation(self):
        assert self.fn("PHASE_4", "PHASE_6") is True

    def test_phase5_vers_phase6(self):
        assert self.fn("PHASE_5", "PHASE_6") is True

    def test_phase6_vers_cloture(self):
        assert self.fn("PHASE_6", "CLOTURE") is True

    def test_saut_de_phase_interdit(self):
        assert self.fn("PHASE_1", "PHASE_3") is False

    def test_retour_en_arriere_interdit(self):
        assert self.fn("PHASE_3", "PHASE_1") is False

    def test_cloture_sans_sortie(self):
        assert self.fn("CLOTURE", "PHASE_1") is False

    def test_etat_inconnu_retourne_false(self):
        assert self.fn("INEXISTANT", "PHASE_2") is False


# ─── calculer_budget_utilise_cycle ────────────────────────────────────────────

class TestCalculerBudgetUtilise:

    def test_zero_si_aucune_transaction(self, svc_db):
        cid = _insert_cycle(svc_db, "2026-05")
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import calculer_budget_utilise_cycle
            result = calculer_budget_utilise_cycle(cid)
        assert result == 0.0

    def test_somme_quantite_x_prix_plus_frais(self, svc_db):
        cid = _insert_cycle(svc_db, "2026-05")
        _insert_transaction(svc_db, cid, quantite=2.0, prix_reel=110.0, frais=1.0)
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import calculer_budget_utilise_cycle
            result = calculer_budget_utilise_cycle(cid)
        # 2 * 110.0 + 1.0 = 221.0
        assert result == pytest.approx(221.0)

    def test_cumul_plusieurs_transactions(self, svc_db):
        cid = _insert_cycle(svc_db, "2026-05")
        _insert_transaction(svc_db, cid, quantite=1.0, prix_reel=100.0, frais=1.0)
        _insert_transaction(svc_db, cid, quantite=0.5, prix_reel=50.0, frais=1.0)
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import calculer_budget_utilise_cycle
            result = calculer_budget_utilise_cycle(cid)
        # (1*100+1) + (0.5*50+1) = 101 + 26 = 127
        assert result == pytest.approx(127.0)


# ─── peut_creer_cycle ─────────────────────────────────────────────────────────

class TestPeutCreerCycle:

    def test_peut_creer_si_aucun_cycle(self, svc_db):
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import peut_creer_cycle
            assert peut_creer_cycle() is True

    def test_ne_peut_pas_creer_si_cycle_ouvert(self, svc_db):
        _insert_cycle(svc_db, "2026-05", etat="PHASE_2")
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import peut_creer_cycle
            assert peut_creer_cycle() is False

    def test_peut_creer_apres_cloture(self, svc_db):
        _insert_cycle(svc_db, "2026-05", etat="CLOTURE")
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import peut_creer_cycle
            assert peut_creer_cycle() is True


# ─── get_budget_restant ───────────────────────────────────────────────────────

class TestGetBudgetRestant:

    def test_retourne_zeros_si_aucun_cycle(self, svc_db):
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import get_budget_restant
            result = get_budget_restant("2026-05")
        assert result["budget_restant"] == 0.0
        assert result["budget_mensuel"] == 0.0

    def test_budget_restant_sans_depense(self, svc_db):
        _insert_cycle(svc_db, "2026-05", budget_mensuel=20.0, budget_utilise=0.0)
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import get_budget_restant
            result = get_budget_restant("2026-05")
        assert result["budget_mensuel"] == 20.0
        assert result["budget_restant"] == 20.0

    def test_budget_restant_apres_depense(self, svc_db):
        _insert_cycle(svc_db, "2026-05", budget_mensuel=20.0, budget_utilise=12.0)
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import get_budget_restant
            result = get_budget_restant("2026-05")
        assert result["budget_restant"] == pytest.approx(8.0)

    def test_carry_over_mois_precedent(self, svc_db):
        # Avril : 20€ budget, 10€ utilisés → 10€ de report en mai
        _insert_cycle(svc_db, "2026-04", budget_mensuel=20.0, budget_utilise=10.0, etat="CLOTURE")
        _insert_cycle(svc_db, "2026-05", budget_mensuel=20.0, budget_utilise=0.0)
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import get_budget_restant
            result = get_budget_restant("2026-05")
        # 20 (mai) + 10 (report avril) - 0 = 30
        assert result["carry_over"] == pytest.approx(10.0)
        assert result["budget_restant"] == pytest.approx(30.0)

    def test_carry_over_nul_si_tout_depense(self, svc_db):
        _insert_cycle(svc_db, "2026-04", budget_mensuel=20.0, budget_utilise=20.0, etat="CLOTURE")
        _insert_cycle(svc_db, "2026-05", budget_mensuel=20.0, budget_utilise=0.0)
        with patch("backend.database.DB_PATH", svc_db):
            from backend.services.sentinelle_service import get_budget_restant
            result = get_budget_restant("2026-05")
        assert result["carry_over"] == 0.0
        assert result["budget_restant"] == pytest.approx(20.0)
