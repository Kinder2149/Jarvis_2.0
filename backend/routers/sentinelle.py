from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import get_connection
from backend.services import sentinelle_service
from typing import Optional

router = APIRouter(prefix="/sentinelle", tags=["sentinelle"])


class PositionCreate(BaseModel):
    ticker: str
    quantite: float
    enveloppe: str
    date_entree: str


class PositionUpdate(BaseModel):
    quantite: float


class WatchlistCreate(BaseModel):
    ticker: str
    niveau_risque: str
    note: Optional[str] = None


class CycleCreate(BaseModel):
    mois: str
    budget_mensuel: float = 20.0


class CycleEtatUpdate(BaseModel):
    etat: str


class CycleDecisionUpdate(BaseModel):
    mode: str
    decision: str


class CycleClotureUpdate(BaseModel):
    resume: Optional[str] = None


class TransactionCreate(BaseModel):
    cycle_id: int
    ticker: str
    quantite: float
    prix_reel: float
    frais: float = 0.0


class PositionUpsert(BaseModel):
    ticker: str
    quantite: float
    prix_unitaire: float
    enveloppe: str
    date_entree: str


class OrdreCreate(BaseModel):
    scenario_choisi: str
    montant: float


@router.get("/positions")
def list_positions():
    """Liste toutes les positions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sentinelle_positions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


@router.get("/positions/valorisation")
async def get_positions_valorisation():
    """Récupère toutes les positions avec valorisation en temps réel."""
    from backend.services.sentinelle_service import _fetch_twelve_data_prices, _fetch_coingecko_prices
    from backend.database import load_config
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sentinelle_positions ORDER BY created_at DESC")
    positions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not positions:
        return {"positions": [], "total_valorisation": 0.0, "total_prix_revient": 0.0, "total_plus_value": 0.0, "total_plus_value_pct": 0.0}
    
    # Séparer actions/ETF et crypto
    stock_tickers = []
    crypto_tickers = []
    CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "ADA", "DOT", "AVAX", "MATIC", "LINK", "UNI"]
    
    for pos in positions:
        ticker = pos["ticker"]
        if ticker in CRYPTO_SYMBOLS:
            crypto_tickers.append(ticker)
        else:
            stock_tickers.append(ticker)
    
    # Récupérer cours actuels
    config = load_config()
    twelve_data_key = config["api_keys"].get("twelve_data_key", "")
    
    stock_prices = await _fetch_twelve_data_prices(stock_tickers, twelve_data_key) if stock_tickers else {}
    crypto_prices = await _fetch_coingecko_prices(crypto_tickers) if crypto_tickers else {}
    
    all_prices = {**stock_prices, **crypto_prices}
    
    # Enrichir chaque position
    positions_enrichies = []
    total_valorisation = 0.0
    total_prix_revient = 0.0
    
    for pos in positions:
        ticker = pos["ticker"]
        quantite = pos["quantite"]
        prix_moyen = pos.get("prix_moyen", 0.0) or 0.0
        prix_revient = pos.get("prix_revient", 0.0) or 0.0
        
        # Si prix_revient pas calculé, le calculer
        if prix_revient == 0.0 and prix_moyen > 0.0:
            prix_revient = quantite * prix_moyen
        
        cours_actuel = all_prices.get(ticker, {}).get("cours", None)
        
        if cours_actuel is not None and cours_actuel > 0:
            valorisation_actuelle = quantite * cours_actuel
            plus_value_latente = valorisation_actuelle - prix_revient
            plus_value_pct = (plus_value_latente / prix_revient * 100) if prix_revient > 0 else 0.0
        else:
            valorisation_actuelle = None
            plus_value_latente = None
            plus_value_pct = None
        
        positions_enrichies.append({
            **pos,
            "cours_actuel": cours_actuel,
            "valorisation_actuelle": valorisation_actuelle,
            "plus_value_latente": plus_value_latente,
            "plus_value_pct": plus_value_pct
        })
        
        if valorisation_actuelle is not None:
            total_valorisation += valorisation_actuelle
        if prix_revient > 0:
            total_prix_revient += prix_revient
    
    total_plus_value = total_valorisation - total_prix_revient
    total_plus_value_pct = (total_plus_value / total_prix_revient * 100) if total_prix_revient > 0 else 0.0
    
    return {
        "positions": positions_enrichies,
        "total_valorisation": total_valorisation,
        "total_prix_revient": total_prix_revient,
        "total_plus_value": total_plus_value,
        "total_plus_value_pct": total_plus_value_pct
    }


@router.post("/positions", status_code=201)
def create_position(data: PositionCreate):
    """Créer une nouvelle position."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sentinelle_positions (ticker, quantite, enveloppe, date_entree)
        VALUES (?, ?, ?, ?)
    """, (data.ticker, data.quantite, data.enveloppe, data.date_entree))
    conn.commit()
    position_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM sentinelle_positions WHERE id = ?", (position_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row)


@router.post("/positions/upsert", status_code=200)
def upsert_position(data: PositionUpsert):
    """Créer ou mettre à jour une position (addition quantité + moyenne pondérée prix)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Vérifier si position existe
    cursor.execute("SELECT * FROM sentinelle_positions WHERE ticker = ?", (data.ticker,))
    existing = cursor.fetchone()
    
    if existing:
        # Mettre à jour : addition quantité + moyenne pondérée prix
        ancienne_quantite = existing["quantite"]
        ancien_prix = existing.get("prix_moyen", 0.0) or 0.0
        nouvelle_quantite = ancienne_quantite + data.quantite
        
        # Moyenne pondérée
        if nouvelle_quantite > 0:
            nouveau_prix_moyen = (
                (ancienne_quantite * ancien_prix + data.quantite * data.prix_unitaire) / nouvelle_quantite
            )
        else:
            nouveau_prix_moyen = 0.0
        
        nouveau_prix_revient = nouvelle_quantite * nouveau_prix_moyen
        
        cursor.execute("""
            UPDATE sentinelle_positions
            SET quantite = ?, prix_moyen = ?, prix_revient = ?, enveloppe = ?, date_entree = ?
            WHERE ticker = ?
        """, (nouvelle_quantite, nouveau_prix_moyen, nouveau_prix_revient, data.enveloppe, data.date_entree, data.ticker))
        conn.commit()
        
        cursor.execute("SELECT * FROM sentinelle_positions WHERE ticker = ?", (data.ticker,))
        row = cursor.fetchone()
        conn.close()
        return dict(row)
    else:
        # Créer nouvelle position
        prix_revient = data.quantite * data.prix_unitaire
        cursor.execute("""
            INSERT INTO sentinelle_positions (ticker, quantite, enveloppe, date_entree, prix_moyen, prix_revient)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data.ticker, data.quantite, data.enveloppe, data.date_entree, data.prix_unitaire, prix_revient))
        conn.commit()
        position_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM sentinelle_positions WHERE id = ?", (position_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row)


@router.patch("/positions/{position_id}")
def update_position(position_id: int, data: PositionUpdate):
    """Mettre à jour la quantité d'une position."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_positions WHERE id = ?", (position_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Position non trouvée")
    
    cursor.execute("""
        UPDATE sentinelle_positions 
        SET quantite = ? 
        WHERE id = ?
    """, (data.quantite, position_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM sentinelle_positions WHERE id = ?", (position_id,))
    updated_row = cursor.fetchone()
    conn.close()
    
    return dict(updated_row)


@router.delete("/positions/{position_id}", status_code=204)
def delete_position(position_id: int):
    """Supprimer une position."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_positions WHERE id = ?", (position_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Position non trouvée")
    
    cursor.execute("DELETE FROM sentinelle_positions WHERE id = ?", (position_id,))
    conn.commit()
    conn.close()
    
    return None


@router.get("/watchlist")
def list_watchlist():
    """Liste la watchlist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sentinelle_watchlist ORDER BY date_ajout DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


@router.post("/watchlist", status_code=201)
def add_to_watchlist(data: WatchlistCreate):
    """Ajouter un actif à la watchlist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO sentinelle_watchlist (ticker, niveau_risque, note)
            VALUES (?, ?, ?)
        """, (data.ticker, data.niveau_risque, data.note))
        conn.commit()
        watchlist_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM sentinelle_watchlist WHERE id = ?", (watchlist_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row)
    except Exception as e:
        conn.close()
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Ce ticker existe déjà dans la watchlist")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{watchlist_id}", status_code=204)
def remove_from_watchlist(watchlist_id: int):
    """Retirer un actif de la watchlist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_watchlist WHERE id = ?", (watchlist_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Actif non trouvé dans la watchlist")
    
    cursor.execute("DELETE FROM sentinelle_watchlist WHERE id = ?", (watchlist_id,))
    conn.commit()
    conn.close()
    
    return None


@router.get("/cycles")
def list_cycles(mois: Optional[str] = None):
    """Liste les cycles (filtrable par mois)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if mois:
        cursor.execute("SELECT * FROM sentinelle_cycles WHERE mois = ? ORDER BY created_at DESC", (mois,))
    else:
        cursor.execute("SELECT * FROM sentinelle_cycles ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


@router.get("/cycles/actif")
def get_cycle_actif():
    """Récupère le cycle en cours (etat != CLOTURE), null si aucun."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sentinelle_cycles 
        WHERE etat != 'CLOTURE' 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


@router.post("/cycles", status_code=201)
def create_cycle(data: CycleCreate):
    """Créer un nouveau cycle."""
    if not sentinelle_service.peut_creer_cycle():
        raise HTTPException(
            status_code=400, 
            detail="Un cycle non clôturé existe déjà. Clôturez-le avant d'en créer un nouveau."
        )
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sentinelle_cycles (mois, budget_mensuel)
        VALUES (?, ?)
    """, (data.mois, data.budget_mensuel))
    conn.commit()
    cycle_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row)


@router.patch("/cycles/{cycle_id}/etat")
def update_cycle_etat(cycle_id: int, data: CycleEtatUpdate):
    """Avancer à la phase suivante."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Cycle non trouvé")
    
    etat_actuel = row["etat"]
    
    if not sentinelle_service.transition_etat_valide(etat_actuel, data.etat):
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail=f"Transition invalide: {etat_actuel} → {data.etat}"
        )
    
    cursor.execute("""
        UPDATE sentinelle_cycles 
        SET etat = ?, updated_at = datetime('now') 
        WHERE id = ?
    """, (data.etat, cycle_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    updated_row = cursor.fetchone()
    conn.close()
    
    return dict(updated_row)


@router.patch("/cycles/{cycle_id}/decision")
def update_cycle_decision(cycle_id: int, data: CycleDecisionUpdate):
    """Enregistrer la décision Phase 4."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Cycle non trouvé")
    
    cursor.execute("""
        UPDATE sentinelle_cycles 
        SET mode = ?, decision = ?, updated_at = datetime('now') 
        WHERE id = ?
    """, (data.mode, data.decision, cycle_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    updated_row = cursor.fetchone()
    conn.close()
    
    return dict(updated_row)


@router.patch("/cycles/{cycle_id}/cloture")
def cloturer_cycle(cycle_id: int, data: CycleClotureUpdate):
    """Clôturer un cycle."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Cycle non trouvé")
    
    if row["etat"] == "CLOTURE":
        conn.close()
        raise HTTPException(status_code=400, detail="Ce cycle est déjà clôturé")
    
    # Calculer le budget utilisé réel
    budget_utilise = sentinelle_service.calculer_budget_utilise_cycle(cycle_id)
    
    cursor.execute("""
        UPDATE sentinelle_cycles 
        SET etat = 'CLOTURE', budget_utilise = ?, updated_at = datetime('now') 
        WHERE id = ?
    """, (budget_utilise, cycle_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    updated_row = cursor.fetchone()
    conn.close()
    
    return dict(updated_row)


@router.get("/transactions")
def list_transactions(cycle_id: Optional[int] = None):
    """Liste les transactions (filtrable par cycle_id)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if cycle_id:
        cursor.execute("SELECT * FROM sentinelle_transactions WHERE cycle_id = ? ORDER BY date_transaction DESC", (cycle_id,))
    else:
        cursor.execute("SELECT * FROM sentinelle_transactions ORDER BY date_transaction DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


@router.post("/transactions", status_code=201)
def create_transaction(data: TransactionCreate):
    """Créer une nouvelle transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Vérifier que le cycle existe
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (data.cycle_id,))
    cycle_row = cursor.fetchone()
    
    if not cycle_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Cycle non trouvé")
    
    cursor.execute("""
        INSERT INTO sentinelle_transactions (cycle_id, ticker, quantite, prix_reel, frais, date_transaction)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.cycle_id, data.ticker, data.quantite, data.prix_reel, data.frais, data.date_transaction))
    conn.commit()
    transaction_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM sentinelle_transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row)


@router.get("/budget/{mois}")
def get_budget_mois(mois: str):
    """Calcule le budget mensuel restant (format YYYY-MM)."""
    budget_info = sentinelle_service.get_budget_restant(mois)
    return budget_info


@router.post("/cycles/{cycle_id}/veille")
async def run_veille_cycle(cycle_id: int):
    """SKILL 1 - Veille : Récupère cours + variations et génère résumé IA."""
    try:
        resultat = await sentinelle_service.run_veille(cycle_id)
        return resultat
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur veille: {str(e)}")


@router.post("/cycles/{cycle_id}/analyse")
async def run_analyse_cycle(cycle_id: int):
    """SKILL 2 - Analyse : Calcule valorisation + allocation + dérives."""
    try:
        resultat = await sentinelle_service.run_analyse(cycle_id)
        return resultat
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse: {str(e)}")


@router.post("/cycles/{cycle_id}/propositions")
async def run_propositions_cycle(cycle_id: int):
    """SKILL 3 - Propositions : Génère 3 scénarios d'investissement avec détection biais."""
    try:
        resultat = await sentinelle_service.run_propositions(cycle_id)
        return resultat
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur propositions: {str(e)}")


@router.post("/cycles/{cycle_id}/ordre")
async def run_ordre_cycle(cycle_id: int, data: OrdreCreate):
    """SKILL 4 - Ordre : Génère paramètres d'ordre précis pour Trade Republic."""
    try:
        resultat = await sentinelle_service.run_ordre(cycle_id, data.scenario_choisi, data.montant)
        return resultat
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur ordre: {str(e)}")


@router.get("/cycles/recent")
def get_cycles_recent():
    """Retourne les 5 derniers cycles, toutes phases confondues."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sentinelle_cycles 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


@router.get("/cycles/actif/count")
def get_cycles_actif_count():
    """Retourne le nombre de cycles dont etat != 'CLOTURE'."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM sentinelle_cycles 
        WHERE etat != 'CLOTURE'
    """)
    row = cursor.fetchone()
    conn.close()
    
    return {"count": row["count"]}


@router.get("/alertes")
def get_alertes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sentinelle_alertes
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/alertes/count")
def get_alertes_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM sentinelle_alertes
        WHERE lu = 0
    """)
    row = cursor.fetchone()
    conn.close()
    return {"count": row["count"]}


@router.patch("/alertes/{alerte_id}/lu")
def mark_alerte_lue(alerte_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sentinelle_alertes
        SET lu = 1
        WHERE id = ?
    """, (alerte_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM sentinelle_alertes WHERE id = ?", (alerte_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    
    return dict(row)


@router.delete("/alertes/lues")
def delete_alertes_lues():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sentinelle_alertes WHERE lu = 1")
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return {"deleted": deleted_count}


@router.post("/alertes/run-check")
async def run_check_alertes_debug():
    """Endpoint de debug pour tester manuellement la vérification des alertes."""
    from backend.services import sentinelle_service
    result = await sentinelle_service.run_check_alertes()
    return result
