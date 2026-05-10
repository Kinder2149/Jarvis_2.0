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
    date_transaction: str


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


@router.put("/positions/{position_id}")
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
